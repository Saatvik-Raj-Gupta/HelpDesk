from __future__ import annotations

import streamlit as st

from src.agent.graph import run_agent_workflow
from src.config import load_settings, startup_checks
from src.ingestion.indexer import get_index_status, index_knowledge_base
from src.llm_provider import build_llm_provider
from src.retrieval.retriever import retrieve_documents
from src.services.answer_generator import build_grounded_answer
from src.triage.classifier import classify_ticket
from src.triage.sample_tickets import SAMPLE_TICKETS


def render_app() -> None:
    settings = load_settings()
    status = startup_checks(settings)
    provider = build_llm_provider(settings)
    provider_status = provider.health_check()

    st.set_page_config(page_title="HelpDesk AI", page_icon="🛠️", layout="wide")
    st.title("🛠️ HelpDesk AI")
    st.caption("Prototype IT support triage and troubleshooting assistant.")

    st.warning(
        "This prototype is for local demonstration only. It does not send emails, change production systems, or modify live tickets."
    )

    overview_col, config_col = st.columns(2)
    with overview_col:
        st.subheader("Overview")
        st.write(
            "The application is designed to classify incoming support tickets, retrieve relevant troubleshooting documentation, "
            "and suggest a grounded resolution for human review."
        )

        try:
            index_result = get_index_status(settings)
            indexed_docs = index_result.indexed_documents
            indexed_chunks = index_result.indexed_chunks
            index_warning = index_result.errors
            if indexed_chunks > 0:
                status_text = f"Indexed and ready ({indexed_chunks} chunks)"
            else:
                status_text = "Not indexed yet"
        except Exception as exc:  # pragma: no cover - runtime guard
            indexed_docs = 0
            indexed_chunks = 0
            index_warning = [str(exc)]
            status_text = "Status unavailable"

        st.markdown(
            f"- Knowledge base status: {status_text}\n"
            "- Retrieval: working with a local Chroma vector index\n"
            "- Agent workflow: LangGraph-based tool orchestration is enabled\n"
            "- Human review: included in the UI flow"
        )

        if index_warning:
            st.caption("Indexing warnings:")
            for warning in index_warning:
                st.warning(warning)

    with config_col:
        st.subheader("Startup status")
        if provider_status.get("ok"):
            st.success(f"LLM connectivity: {provider_status.get('message')}")
        else:
            st.warning(f"LLM connectivity: {provider_status.get('message')}")

        if status["warnings"]:
            st.warning("Configuration warnings were detected:")
            for warning in status["warnings"]:
                st.write(f"- {warning}")
        else:
            st.success("All basic project checks passed.")

        st.json({
            "app_name": settings.app_name,
            "app_environment": settings.app_environment,
            "llm_provider": settings.llm_provider,
            "llm_model": settings.llm_model,
            "embedding_model": settings.embedding_model,
            "streamlit_server_port": settings.streamlit_server_port,
        })

    tabs = st.tabs(["Overview", "Ticket triage", "Knowledge base", "Evaluation"])

    with tabs[0]:
        st.info("Gemini is configured and the local knowledge base is available for retrieval in this phase.")

    with tabs[1]:
        examples = [ticket["name"] for ticket in SAMPLE_TICKETS]
        selected_example = st.selectbox("Example tickets", ["Custom ticket", *examples])
        sample_ticket = SAMPLE_TICKETS[0]["text"]
        ticket_value = sample_ticket if selected_example == "Custom ticket" else next(
            ticket["text"] for ticket in SAMPLE_TICKETS if ticket["name"] == selected_example
        )
        ticket_input = st.text_area("Support ticket", value=ticket_value, height=220, placeholder="Paste a support ticket here...")

        if st.button("Run Triage"):
            try:
                result = classify_ticket(ticket_input)
                st.subheader("Classification result")
                st.write(f"Category: {result.category}")
                st.write(f"Priority: {result.priority}")
                st.write(f"Issue summary: {result.short_issue_summary}")
                st.write("Evidence:")
                for item in result.evidence:
                    st.write(f"- {item}")
                st.write(f"Confidence: {result.confidence_explanation}")
            except ValueError as exc:
                st.error(str(exc))

        if st.button("Run Agent Workflow"):
            try:
                workflow_result = run_agent_workflow(ticket_input, settings=settings)
                st.subheader("Agent workflow output")
                st.write(workflow_result["classification"])
                st.write("Tool activity:")
                for item in workflow_result["tool_activity"]:
                    status = "ok" if item.get("ok", True) else "failed"
                    st.write(f"- {item['tool']} ({status}): {item.get('payload')}")
                st.write("Suggested action:")
                st.write(workflow_result["answer"].get("issue_summary", "No answer generated."))
                if workflow_result["errors"]:
                    st.warning("Errors: " + "; ".join(workflow_result["errors"]))
            except Exception as exc:  # pragma: no cover - runtime guard
                st.error(f"Agent workflow failed: {exc}")

    with tabs[2]:
        index_button = st.button("Index Knowledge Base")
        if index_button:
            try:
                result = index_knowledge_base(settings, force=True)
                st.success(f"Indexed {result.indexed_documents} documents and {result.indexed_chunks} chunks.")
                if result.errors:
                    for error in result.errors:
                        st.warning(error)
            except Exception as exc:  # pragma: no cover - runtime guard
                st.error(f"Indexing failed: {exc}")

        query = st.text_input(
            "Search the local knowledge base",
            value="After upgrading a Java dependency, the application fails to start because of a missing class.",
        )
        if st.button("Run search") and query:
            try:
                results = retrieve_documents(settings, query, top_k=3)
                answer = build_grounded_answer(query, results)
                st.subheader("Retrieved passages")
                for index, result in enumerate(results, start=1):
                    st.markdown(f"### Result {index} (score: {result['score']})")
                    st.write(result["source_name"])
                    st.write(result["content"])
                st.subheader("Grounded answer")
                st.write(answer["issue_summary"])
                st.write("Citations:")
                for citation in answer["citations"]:
                    st.write(f"- {citation['source']}: {citation['content']}")
            except Exception as exc:  # pragma: no cover - runtime guard
                st.error(f"Retrieval failed: {exc}")

        st.caption("The sample knowledge base includes troubleshooting documentation for dependency, runtime, and access issues.")

    with tabs[3]:
        st.button("Run evaluation set", disabled=True)
        st.caption("Evaluation and sample dataset support will be added in later phases.")


if __name__ == "__main__":
    render_app()
