#!/usr/bin/env python
import asyncio
import sys
import json
import requests
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MinioMCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: ClientSession | None = None
        self.exit_stack = AsyncExitStack()

        # Ollama configuration
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model = "llama3.2:latest"
        
    async def connect_to_server(self, server_script_path: str):
        """Connect to the MinIO MCP server
        
        Args:
            server_script_path: Path to the server.py file
        """
        if not server_script_path.endswith('.py'):
            raise ValueError("MinIO server script must be a .py file")

        # Set up the server process
        server_params = StdioServerParameters(
            command="python",
            args=[server_script_path],
            env=None
        )

        # Connect to the server
        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        # Initialize the session
        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to MinIO MCP Server with tools:", [tool.name for tool in tools])
        return tools
        
    async def process_query_with_ollama(self, query: str) -> str:
        """Process a query using Ollama and available MinIO tools"""
        
        # Get available tools from the server
        response = await self.session.list_tools()
        available_tools = []
        
        for tool in response.tools:
            tool_info = {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema.get("properties", {}) if tool.inputSchema else {}
            }
            available_tools.append(tool_info)

        # Create system prompt with tool information
        system_prompt = f"""You are a helpful assistant with access to MinIO storage management tools.

Available tools:
{json.dumps(available_tools, indent=2)}

When the user asks about MinIO operations (listing buckets, getting bucket info, listing objects), you should:
1. Identify which tool(s) to use
2. Determine the parameters needed
3. Respond with a JSON object in this format:
{{"tool_call": {{"name": "tool_name", "parameters": {{"param1": "value1"}}}}}}

If no tool call is needed, respond normally with helpful information."""  # noqa: E501

        # Initial Ollama API call
        data = {
            "model": self.model,
            "prompt": query,
            "system": system_prompt,
            "stream": False
        }

        try:
            response = requests.post(self.ollama_url, json=data)
            response.raise_for_status()
            ollama_response = response.json()
            response_text = ollama_response.get("response", "")
            
            # Check if the response contains a tool call
            if "tool_call" in response_text:
                try:
                    # Extract JSON from response
                    json_start = response_text.find("{")
                    json_end = response_text.rfind("}") + 1
                    tool_call_json = json.loads(response_text[json_start:json_end])
                    
                    if "tool_call" in tool_call_json:
                        tool_name = tool_call_json["tool_call"]["name"]
                        tool_params = tool_call_json["tool_call"].get("parameters", {})
                        
                        print(f"\n🔧 Using tool: {tool_name} with parameters: {tool_params}")
                        
                        # Execute the tool
                        tool_result = await self.session.call_tool(tool_name, tool_params)
                        
                        # Get a follow-up response from Ollama with the results
                        follow_up_prompt = f"""The tool {tool_name} returned this result:
{tool_result.content}

Please provide a user-friendly summary of this information."""
                        
                        follow_up_data = {
                            "model": self.model,
                            "prompt": follow_up_prompt,
                            "system": "You are a helpful assistant. Provide clear, user-friendly summaries of MinIO tool results.",
                            "stream": False
                        }
                        
                        follow_up_response = requests.post(self.ollama_url, json=follow_up_data)
                        if follow_up_response.status_code == 200:
                            follow_up_result = follow_up_response.json()
                            return f"🔧 Tool Result:\n{tool_result.content}\n\n📝 Summary:\n{follow_up_result.get('response', '')}"
                        else:
                            return f"🔧 Tool Result:\n{tool_result.content}"
                            
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Could not parse tool call: {e}")
                    return response_text
            
            return response_text
            
        except Exception as e:
            return f"Error communicating with Ollama: {str(e)}"
    
    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\n🗄️  MinIO Assistant Started!")
        print("Ask about your MinIO storage, or type 'quit' to exit.")
        print("Example queries:")
        print("  - 'List all my buckets'")
        print("  - 'Show me information about bucket named photos'")
        print("  - 'What objects are in the documents bucket?'")
        print("  - 'List the first 10 objects in my-data bucket'")

        while True:
            try:
                query = input("\n💬 Query: ").strip()

                if query.lower() == 'quit':
                    break

                print("\n🤔 Processing your query...")
                response = await self.process_query_with_ollama(query)
                print(f"\n🤖 {response}")

            except Exception as e:
                print(f"\n❌ Error: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()


async def main():
    if len(sys.argv) < 2:
        print("Usage: python minio_client.py <path_to_server.py>")
        print("Example: python minio_client.py src/minio_mcp/server.py")
        sys.exit(1)

    client = MinioMCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())