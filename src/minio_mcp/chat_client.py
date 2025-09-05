#!/usr/bin/env python3
"""MinIO Chat Client - Natural language interface to MinIO via Ollama + MCP"""

import asyncio
import json
from contextlib import AsyncExitStack

import requests
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MinioChat:
    def __init__(self):
        self.session: ClientSession | None = None
        self.exit_stack = AsyncExitStack()
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model = "llama3.2:latest"

        # Enhanced context tracking (Weather Server style)
        self.buckets: list[str] = []
        self.current_bucket: str | None = None
        self.conversation_history: list[dict] = []  # Track conversation like weather server
        self.last_tool_results: dict = {}  # Store recent tool results

    async def connect(self) -> None:
        """Connect to MinIO MCP server"""
        server_params = StdioServerParameters(
            command="python",
            args=["src/minio_mcp/server.py"]
        )

        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        await self.session.initialize()
        print("🔗 Connected to MinIO MCP Server")

    def build_system_prompt(self) -> str:
        """Build system prompt with current context - Weather Server Style"""
        # Get exact tools from server (like weather server does)
        tools_info = """AVAILABLE TOOLS (use exact names):

1. list_buckets() 
   - Lists all available buckets in MinIO
   - No parameters required
   - Returns: JSON with buckets array

2. get_bucket_info(bucket_name)
   - Gets detailed information about a specific bucket
   - Required: bucket_name (string) - exact bucket name
   - Returns: Bucket details, size, object count

3. list_objects(bucket_name, prefix="", limit=25)
   - Lists objects in a specific bucket
   - Required: bucket_name (string) - exact bucket name  
   - Optional: prefix (string) - filter by prefix
   - Optional: limit (integer) - max objects to return
   - Returns: List of objects with metadata

4. create_bucket(bucket_name)
   - Creates a new bucket
   - Required: bucket_name (string) - new bucket name
   - Returns: Success/error message

5. delete_bucket(bucket_name, force=False)
   - Deletes a bucket
   - Required: bucket_name (string) - bucket to delete
   - Optional: force (boolean) - delete with objects
   - Returns: Success/error message"""

        # Context information (like weather server maintains state)
        context = ""
        if self.buckets:
            context += "\nCURRENT CONTEXT:\n"
            context += f"Available buckets: {', '.join(self.buckets)}\n"
            if self.current_bucket:
                context += f"Last accessed bucket: {self.current_bucket}\n"
        else:
            context += "\nCURRENT CONTEXT: No buckets discovered yet. Use list_buckets first.\n"

        return f"""You are a MinIO storage assistant with access to MinIO management tools.

{tools_info}
{context}

CRITICAL RULES:
1. Use EXACT tool names from the list above
2. When user mentions "the bucket", "that bucket", or "my bucket" - use the last accessed bucket from context
3. ALWAYS use real bucket names from context, NEVER use placeholders like <bucket-name> or <your-bucket-name>
4. If you need to list buckets first, do that before other operations
5. Respond with JSON format: {{"tool_call": {{"name": "exact_tool_name", "parameters": {{"param": "real_value"}}}}}}

EXAMPLES:
- User: "list my buckets" → {{"tool_call": {{"name": "list_buckets", "parameters": {{}}}}}}
- Context has "test" bucket, User: "show info for test" → {{"tool_call": {{"name": "get_bucket_info", "parameters": {{"bucket_name": "test"}}}}}}
- Context has "photos" bucket, User: "list objects in that bucket" → {{"tool_call": {{"name": "list_objects", "parameters": {{"bucket_name": "photos"}}}}}}"""

    async def call_ollama(self, query: str) -> str:
        """Call Ollama API"""
        data = {
            "model": self.model,
            "prompt": query,
            "system": self.build_system_prompt(),
            "stream": False
        }

        response = requests.post(self.ollama_url, json=data)
        return response.json().get("response", "")

    def extract_tool_call(self, text: str) -> dict | None:
        """Extract tool call from Ollama response"""
        if "tool_call" not in text:
            return None

        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            data = json.loads(text[start:end])
            return data.get("tool_call")
        except:
            return None

    def update_context(self, tool_name: str, params: dict, result: str) -> None:
        """Update context based on tool results - Enhanced like Weather Server"""
        # Store this interaction in conversation history
        self.conversation_history.append({
            "tool": tool_name,
            "params": params,
            "result": result[:200] + "..." if len(result) > 200 else result
        })

        # Keep only last 5 interactions to prevent memory bloat
        if len(self.conversation_history) > 5:
            self.conversation_history.pop(0)

        # Update specific context based on tool type
        if tool_name == "list_buckets":
            try:
                data = json.loads(result)
                self.buckets = [b["name"] for b in data.get("buckets", [])]
                print(f"🧠 Context updated: Found buckets: {self.buckets}")

                # If only one bucket, make it current (like weather server logic)
                if len(self.buckets) == 1:
                    self.current_bucket = self.buckets[0]
                    print(f"🧠 Auto-selected bucket: {self.current_bucket}")
            except Exception as e:
                print(f"⚠️  Failed to parse list_buckets result: {e}")

        elif tool_name in ["get_bucket_info", "list_objects", "create_bucket"]:
            bucket = params.get("bucket_name")
            if bucket and bucket in self.buckets:
                self.current_bucket = bucket
                print(f"🧠 Current bucket set to: {self.current_bucket}")

        # Store tool results for reference
        self.last_tool_results[tool_name] = {
            "params": params,
            "result": result,
            "success": not result.startswith("Error")
        }

    async def process_query(self, query: str) -> str:
        """Process user query"""
        # Get Ollama response
        response = await self.call_ollama(query)

        # Check for tool call
        tool_call = self.extract_tool_call(response)
        if not tool_call:
            return response

        # Execute tool
        tool_name = tool_call["name"]
        params = tool_call.get("parameters", {})

        print(f"🔧 {tool_name}({params})")

        try:
            result = await self.session.call_tool(tool_name, params)
            # Fix: Extract text content from MCP response
            content_text = str(result.content[0].text) if result.content else str(result.content)
            self.update_context(tool_name, params, content_text)
            return f"✅ {content_text}"
        except Exception as e:
            return f"❌ Error: {e}"

    async def chat(self) -> None:
        """Interactive chat loop"""
        print("\n🗄️  MinIO Assistant")
        print("Examples: 'list buckets', 'show info for test bucket', 'quit'")

        while True:
            try:
                query = input("\n💬 ").strip()
                if query.lower() in ['quit', 'exit']:
                    break

                if query:
                    response = await self.process_query(query)
                    print(f"🤖 {response}")

            except KeyboardInterrupt:
                break

    async def cleanup(self) -> None:
        """Clean up resources"""
        await self.exit_stack.aclose()


async def async_main():
    """Async main entry point"""
    client = MinioChat()

    try:
        await client.connect()
        await client.chat()
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Ensure Ollama is running: ollama serve")
    finally:
        await client.cleanup()


def main():
    """Synchronous main entry point for CLI"""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
