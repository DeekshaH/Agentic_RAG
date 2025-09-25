import streamlit as st
from dotenv import load_dotenv
import asyncio
import sys
import os
import json
from datetime import datetime
from langchain_core.documents import Document

# Load environment variables
load_dotenv()

# Streamlit app configuration
st.set_page_config(page_title="Adaptive RAG System", page_icon="🤖", layout="wide")

# --- Utility functions ---
def format_response(result):
    """Extract response from workflow result."""
    if isinstance(result, dict) and "generation" in result:
        return result["generation"]
    elif isinstance(result, dict) and "answer" in result:
        return result["answer"]
    else:
        return str(result)

def log_feedback(question, answer, rating):
    """Log user feedback to a file."""
    feedback_entry = {
        "timestamp": datetime.now().isoformat(),
        "question": question,
        "answer": answer,
        "rating": rating
    }
    feedback_dir = "logs"
    feedback_file = os.path.join(feedback_dir, "feedback_log.txt")
    try:
        os.makedirs(feedback_dir, exist_ok=True)
        with open(feedback_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(feedback_entry) + "\n")
        return f"✅ Feedback logged successfully: {rating}"
    except Exception as e:
        return f"⚠️ Failed to log feedback: {str(e)}"

# --- Initialize session state ---
if "query_history" not in st.session_state:
    st.session_state.query_history = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "feedback_status" not in st.session_state:
    st.session_state.feedback_status = ""
if "current_answer" not in st.session_state:
    st.session_state.current_answer = ""
if "current_question" not in st.session_state:
    st.session_state.current_question = ""
if "thread_id" not in st.session_state:
    st.session_state.thread_id = f"user_session_{datetime.now().timestamp()}"  # Unique per session

# Title
st.title("🤖 Adaptive RAG System")

# Sidebar for history
with st.sidebar:
    st.subheader("Query History")
    if st.session_state.query_history:
        for i, entry in enumerate(st.session_state.query_history):
            with st.expander(f"Q{i+1}: {entry['question']}", expanded=False):
                st.markdown(f"**Answer:** {entry['answer']}")
    else:
        st.info("No queries yet.")

# Input field
question = st.text_input("Enter your question:", placeholder="e.g., What are AI agents?")

col1, col2 = st.columns(2)
with col1:
    if st.button("Get Answer"):
        if not question.strip():
            st.error("Please enter a valid question.")
        else:
            loop = None
            try:
                with st.spinner("Processing..."):
                    st.session_state.last_result = None
                    st.session_state.feedback_status = ""
                    st.session_state.current_answer = ""
                    st.session_state.current_question = question

                    # Lazy import workflow
                    try:
                        from src.workflow.graph import app
                    except ImportError as e:
                        st.error(f"Failed to import workflow: {str(e)}")
                        st.stop()

                    # Ensure event loop
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    # Process query
                    result = None
                    config = {
                        "configurable": {"thread_id": st.session_state.thread_id},
                        "recursion_limit": 50
                    }
                    print(f"DEBUG: Config passed to app.stream: {config}")  # Debug
                    try:
                        for output in app.stream({"question": question}, config=config):
                            for _, value in output.items():
                                result = value
                        st.session_state.last_result = result
                    except Exception as e:
                        st.warning(f"Processing error: {str(e)}")

                    if loop and not loop.is_closed():
                        loop.close()

                    if result:
                        answer = format_response(result)
                        st.session_state.current_answer = answer
                        st.session_state.query_history.append({"question": question, "answer": answer})

                        st.markdown(f"**Answer:** {answer}")
                        st.success("Answer generated!")

                        # Show retrieved docs (unique URLs only, no snippets)
                        if result.get("documents"):
                            st.subheader("Retrieved Documents")
                            unique_sources = set()
                            for doc in result.get("documents", []):
                                source = doc.metadata.get("source", "Unknown Source")
                                unique_sources.add(source)
                            for i, source in enumerate(sorted(unique_sources), 1):
                                st.markdown(f"**Doc {i}: {source}**")

            except Exception as e:
                st.error(f"Error: {str(e)}")
            finally:
                if loop and not loop.is_closed():
                    loop.close()
                sys.stdout = sys.__stdout__

with col2:
    if st.button("Clear History"):
        st.session_state.query_history = []
        st.session_state.last_result = None
        st.session_state.feedback_status = ""
        st.session_state.current_answer = ""
        st.session_state.current_question = ""
        st.session_state.thread_id = f"user_session_{datetime.now().timestamp()}"  # New thread_id
        st.rerun()

# Feedback buttons
if st.session_state.last_result:
    if st.session_state.current_answer and st.session_state.current_question:
        st.markdown("**Rate this answer:**")
        fb_col1, fb_col2 = st.columns(2)
        with fb_col1:
            if st.button("👍 Thumbs Up"):
                st.session_state.feedback_status = log_feedback(
                    st.session_state.current_question,
                    st.session_state.current_answer,
                    "positive"
                )
        with fb_col2:
            if st.button("👎 Thumbs Down"):
                st.session_state.feedback_status = log_feedback(
                    st.session_state.current_question,
                    st.session_state.current_answer,
                    "negative"
                )

# Show feedback status
if st.session_state.feedback_status:
    if "Failed" in st.session_state.feedback_status:
        st.warning(st.session_state.feedback_status)
    else:
        st.success(st.session_state.feedback_status)