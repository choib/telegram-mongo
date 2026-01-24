
import asyncio
import logging
import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

# Mock the logger to avoid excessive output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_two_step_rag_flow():
    """
    Test the two-step RAG flow by streaming events from the agent workflow.
    """
    from src.agents import stream_agent_workflow
    
    query = "알선수재와 알선수뢰의 차이는 무엇입니까?" # User's reported query
    context = ""
    
    print(f"\nTesting Two-Step RAG Flow with query: '{query}'")
    print("-" * 50)
    
    nodes_executed = []
    output = {}
    
    try:
        async for event in stream_agent_workflow(query, context):
            event_type = event["event"]
            
            # Look for node execution events from langgraph
            if event_type == "on_chain_start":
                node_name = event.get("metadata", {}).get("langgraph_node")
                if node_name and node_name not in nodes_executed:
                    nodes_executed.append(node_name)
                    print(f"Executing node: {node_name}")
            
            # Capture final output
            if event_type == "on_chain_end":
                data = event.get("data", {}).get("output", {})
                if isinstance(data, dict) and "final_response" in data:
                    output = data
    
    except Exception as e:
        print(f"Error during flow test: {e}")
        import traceback
        traceback.print_exc()

    print("\nWorkflow Results:")
    print(f"Analyzed Query: {output.get('analyzed_query', 'N/A')}")
    print(f"Agent Flow: {output.get('agent_flow', [])}")
    print(f"Final Response Length: {len(output.get('final_response', ''))}")
    
    print("-" * 50)
    print(f"Nodes executed in order: {nodes_executed}")
    
    # Verification assertions
    expected_entry = "analyze"
    if nodes_executed and nodes_executed[0] == expected_entry:
        print(f"✅ PASS: Workflow started with '{expected_entry}' node.")
    else:
        print(f"❌ FAIL: Workflow did not start with '{expected_entry}' node. Got: {nodes_executed[0] if nodes_executed else 'None'}")

    if "analyze" in nodes_executed and "judge" in nodes_executed and "retrieval" in nodes_executed:
        print("✅ PASS: 'analyze', 'judge', and 'retrieval' nodes were executed.")
    else:
        print(f"❌ FAIL: Missing nodes. Executed: {nodes_executed}")

    if len(output.get('agent_flow', [])) > 0:
        print(f"✅ PASS: Agent flow is correctly populated: {output['agent_flow']}")
    else:
        print(f"❌ FAIL: Agent flow is empty!")

if __name__ == "__main__":
    asyncio.run(test_two_step_rag_flow())
