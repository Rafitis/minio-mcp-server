#!/usr/bin/env python
"""
Enterprise MinIO MCP Client
===========================
This script connects your Enterprise LLM to a MinIO MCP Server, allowing natural language
interaction with MinIO storage operations.

Architecture:
User Query → Enterprise LLM (decides tool) → MCP Client (executes) → MinIO Server → Results → LLM (formats) → User
"""

import asyncio
import sys
from typing import Any, Optional, List, Dict
from contextlib import AsyncExitStack
import os
from dotenv import load_dotenv
import json 

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI 

load_dotenv()

class MinioMCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.llm_provider_name = "Enterprise LLM (Sigma)"

        # --- ENTERPRISE LLM: The "Brain" that decides which tools to use ---
        # Configure your enterprise LLM as an OpenAI-compatible client
        self.enterprise_llm_client = OpenAI(
            api_key="banaan",  # Enterprise LLM might not need authentication
            base_url="http://llm-service.gruposigma.local/v1"  # Your company's LLM endpoint
        )
        

    async def connect_to_server(self, server_script_path: str):
        """
        Connect to the MinIO MCP server and discover available tools
        This is like getting the "menu" of what the MinIO server can do
        """
        if not server_script_path.endswith('.py'):
            raise ValueError("MinIO server script must be a .py file")

        # --- STEP 1: Launch the MinIO MCP Server as a subprocess ---
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[server_script_path],
            env=os.environ.copy()
        )

        # --- STEP 2: Establish stdio communication channel ---
        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        # --- STEP 3: Initialize MCP session and discover available tools ---
        await self.session.initialize()
        response = await self.session.list_tools()  # Ask server: "What tools do you have?"
        tools = response.tools
        print(f"\nConnected to MinIO MCP Server. LLM Provider: {self.llm_provider_name}. Available tools: {[tool.name for tool in tools]}")

    async def process_query(self, query: str) -> str:
        """
        THE CORE LOGIC: Process user query through Enterprise LLM + MinIO tools
        
        Flow: User asks → LLM decides tool → Execute tool → LLM formats result → User
        """
        if not self.enterprise_llm_client:
            return "Error: Enterprise LLM client not initialized."

        final_response_parts = []

        # --- PHASE 1: TOOL DISCOVERY - Get the "menu" of available MinIO tools ---
        mcp_tools_response = await self.session.list_tools()  # Ask MinIO server: "What can you do?"
        tool_descriptions_for_prompt = []
        if mcp_tools_response and mcp_tools_response.tools:
            for tool in mcp_tools_response.tools:
                schema_str = "No input schema defined"
                if tool.inputSchema and isinstance(tool.inputSchema, dict):
                    schema_str = json.dumps(tool.inputSchema)
                elif tool.inputSchema:
                    schema_str = str(tool.inputSchema)
                # Build tool descriptions for the LLM to understand what's available
                tool_descriptions_for_prompt.append(f"  - Name: {tool.name}\n    Description: {tool.description}\n    Input Schema (parameters as JSON object): {schema_str}")

        # --- PHASE 2: BUILD SYSTEM PROMPT - Tell LLM what tools are available and how to use them ---
        tools_info_prompt_section = "You are a helpful MinIO storage assistant. You have access to the following tools to help with MinIO object storage operations:\n" + "\n".join(tool_descriptions_for_prompt)
        tools_info_prompt_section += (
            "\n\nBased on the user's query, decide if a tool is needed. "
            "If a tool can help, respond ONLY with the tool call formatted EXACTLY like this (including the 'TOOL_CALL:' prefix and JSON structure, ensure parameters is a JSON object): "
            "TOOL_CALL: {\"tool_name\": \"<tool_name_here>\", \"parameters\": {<parameters_here_as_json_object>}}. "
            "If you don't need a tool, or if the query is not storage-related and cannot be answered by tools, just answer the query directly based on your general knowledge. "
            "If a tool requires specific parameters (like bucket_name) and they are not provided, you can ask the user for them, or state you need them to proceed with the tool."
        )

        # --- PHASE 3: FIRST LLM CALL - Ask LLM: "What tool should I use for this query?" ---
        enterprise_llm_first_pass_messages = [
            {"role": "system", "content": tools_info_prompt_section},  # The "menu" of tools
            {"role": "user", "content": f"User Query: {query}"}       # User's request
        ]

        try:
            # Call your Enterprise LLM to decide which tool to use
            first_pass_completion = self.enterprise_llm_client.chat.completions.create(
                model="sigmaai/llm-prod",  # Your company's LLM model
                messages=enterprise_llm_first_pass_messages,
                max_tokens=500 
            )
            first_pass_text = first_pass_completion.choices[0].message.content.strip()
            

        except Exception as e:
            print(f"Error calling Enterprise LLM API (first pass): {e}", file=sys.stderr)
            return f"Error processing query with Enterprise LLM (first pass): {e}"

        # --- PHASE 4: DECISION PROCESSING - Did LLM decide to use a tool? ---
        if first_pass_text.startswith("TOOL_CALL:"):
            try:
                # --- PHASE 5: PARSE TOOL DECISION - Extract which tool and parameters ---
                tool_call_json_str = first_pass_text.replace("TOOL_CALL:", "").strip()
                tool_call_data = json.loads(tool_call_json_str)
                tool_name = tool_call_data.get("tool_name")        # e.g., "list_buckets"
                tool_parameters = tool_call_data.get("parameters", {})  # e.g., {"bucket_name": "photos"}

                if not tool_name:
                    raise ValueError("Invalid TOOL_CALL format from LLM: 'tool_name' missing.")
                if not isinstance(tool_parameters, dict):
                     raise ValueError(f"Invalid TOOL_CALL format from LLM: 'parameters' is not a JSON object. Got: {tool_parameters}")

                final_response_parts.append(f"[Enterprise LLM decided to use tool: {tool_name} with parameters: {json.dumps(tool_parameters)}]")

                # --- PHASE 6: TOOL EXECUTION - Actually call the MinIO server ---
                mcp_tool_result = await self.session.call_tool(tool_name, tool_parameters)  # Execute on MinIO!
                tool_result_content = str(mcp_tool_result.content)  # Raw MinIO response
                final_response_parts.append(f"[Tool {tool_name} result: {tool_result_content}]")

                # --- PHASE 7: SECOND LLM CALL - Ask LLM to format the raw result nicely ---
                enterprise_llm_second_pass_messages = [
                    {"role": "system", "content": "You are a helpful MinIO storage assistant. You have received the result from a tool call. Use this information to formulate a comprehensive, natural language answer to the user's original query."},
                    {"role": "user", "content": f"Original query: '{query}'\nTool used: '{tool_name}'\nTool parameters: {json.dumps(tool_parameters)}\nTool result: '{tool_result_content}'\n\nPlease provide the final answer to the user."},
                ]
               
                # Second call to LLM: "Format this raw data nicely for the user"
                second_pass_completion = self.enterprise_llm_client.chat.completions.create(
                    model="sigmaai/llm-prod",  # Your company's LLM model
                    messages=enterprise_llm_second_pass_messages,
                    max_tokens=1500
                )
                final_answer_text = second_pass_completion.choices[0].message.content.strip()
                final_response_parts.append(f"\n{final_answer_text}")

            except json.JSONDecodeError as jde:
                final_response_parts.append(f"\n[LLM provided an invalid JSON for TOOL_CALL: {tool_call_json_str}. Error: {jde}]")
                final_response_parts.append("I tried to use a tool but received an improperly formatted instruction. Could you try rephrasing?")
            except ValueError as ve:
                final_response_parts.append(f"\n[Error parsing TOOL_CALL: {ve}]")
                final_response_parts.append("I tried to use a tool but encountered an issue with its specification. Could you try rephrasing?")
            except Exception as e:
                final_response_parts.append(f"\n[Error executing tool or during second Enterprise LLM call: {type(e).__name__} - {e}]")
                final_response_parts.append("Sorry, I encountered an error while trying to use a tool to answer your question.")
        else: 
            # --- PHASE 8: NO TOOL NEEDED - LLM answered directly ---
            final_response_parts.append(first_pass_text)

        return "\n".join(filter(None, final_response_parts))

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMinIO Storage Assistant Started!")
        print(f"Using LLM Provider: {self.llm_provider_name}")
        print("Ask about MinIO storage operations, or type 'quit' to exit.")
        print("Example queries:")
        print("  - 'List all my buckets'")
        print("  - 'Create a bucket called my-photos'")
        print("  - 'Show me the objects in my-data bucket'")
        print("  - 'Get information about the test bucket'")
        print("  - 'Delete the old-files bucket'")

        while True:
            try:
                query = input("\nMinIO Query: ").strip()
                if not query:
                    continue
                if query.lower() == 'quit':
                    break

                print("\nProcessing your query...")
                response = await self.process_query(query)
                print("\n" + response)

            except KeyboardInterrupt:
                print("\nExiting chat loop...")
                break
            except Exception as e:
                print(f"\nAn error occurred in the chat loop: {type(e).__name__} - {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        print("Cleaning up resources...")
        await self.exit_stack.aclose()
        print("Cleanup complete.")

async def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.executable} {os.path.basename(__file__)} <path_to_minio_server.py>")
        print(f"Example: {sys.executable} {os.path.basename(__file__)} ../src/minio_mcp/server.py")
        sys.exit(1)

    server_path = sys.argv[1]
    if not os.path.exists(server_path):
        print(f"Error: Server script not found at {server_path}")
        sys.exit(1)
    if not os.path.isfile(server_path) or not server_path.endswith(".py"):
        print(f"Error: Server path {server_path} must be a Python file.")
        sys.exit(1)

    client = MinioMCPClient()
    try:
        await client.connect_to_server(os.path.abspath(server_path))
        await client.chat_loop()
    except Exception as e:
        print(f"An unhandled error occurred: {type(e).__name__} - {str(e)}", file=sys.stderr)
    finally:
        await client.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nApplication terminated by user.")
    except Exception as e:
        print(f"Critical error during startup/shutdown: {type(e).__name__} - {e}", file=sys.stderr)