from dotenv import load_dotenv
from src.workflow.graph import app

load_dotenv()

def format_response(result):
    """Extract response from workflow result."""
    if isinstance(result, dict) and "generation" in result:
        return result["generation"]
    elif isinstance(result, dict) and "answer" in result:
        return result["answer"]
    else:
        return str(result)

def main():
    """CLI for adaptive RAG system."""
    print("Adaptive RAG System")
    print("Type 'quit' to exit.\n")
    
    # Fixed thread_id for session state; can prompt for multi-user
    thread_id = "user_session_1"  # Or input("Enter session ID: ") for multi-user
    
    while True:
        try:
            question = input("Question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q', '']:
                break
                
            print("Processing...")
            config = {"configurable": {"thread_id": thread_id}}  # Pass config for state
            result = None
            for output in app.stream({"question": question}, config=config):  # Fix: named config
                for key, value in output.items():
                    result = value
                    
            if result:
                print(f"\nAnswer: {format_response(result)}")
                print("\nRetrieved Documents")
                # Collect unique sources
                unique_sources = set()
                for doc in result.get("documents", []):
                    source = doc.metadata.get("source", "Unknown Source")
                    unique_sources.add(source)
                
                # Display unique sources
                for i, source in enumerate(sorted(unique_sources), 1):
                    print(f"Doc {i}: {source}")
                print("\nAnswer generated!")
            else:
                print("No response generated.")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()