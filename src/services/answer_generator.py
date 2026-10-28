from __future__ import annotations


def build_grounded_answer(query: str, passages: list[dict]) -> dict:
    if not passages:
        return {
            "issue_summary": "No relevant information was found in the local knowledge base.",
            "relevant_evidence": [query],
            "retrieved_knowledge": [],
            "suggested_diagnostic_steps": [
                "Confirm the exact error and version information from the ticket.",
                "Check whether the same dependency or runtime issue appears in the support docs.",
                "Escalate to a human reviewer if the cause is still ambiguous.",
            ],
            "proposed_resolution": "No supported resolution could be inferred from the available knowledge base.",
            "citations": [],
            "missing_information": "The available documentation did not contain a strong match for this query.",
            "human_review_recommended": True,
        }

    citations = [
        {"source": item["source_name"], "content": item["content"][:220]}
        for item in passages[:3]
    ]

    summary = f"The most relevant retrieved documentation suggests the ticket is related to {passages[0]['source_name']}."
    evidence = [
        {
            "source": item["source_name"],
            "excerpt": item["content"][:260],
            "score": item["score"],
        }
        for item in passages[:3]
    ]

    return {
        "issue_summary": summary,
        "relevant_evidence": evidence,
        "retrieved_knowledge": [item["content"][:260] for item in passages[:3]],
        "suggested_diagnostic_steps": [
            "Review the cited troubleshooting passages and compare them to the reported environment.",
            "Verify the specific application version, framework version, and dependency versions in the ticket.",
            "Apply the recommended mitigation only after confirming it matches the local configuration.",
        ],
        "proposed_resolution": "Use the retrieved documentation as supporting evidence, not as an automatic fix.",
        "citations": citations,
        "missing_information": "The answer is only as reliable as the matched retrieved passages and should be checked by a human reviewer.",
        "human_review_recommended": True,
    }
