from workflow.state_machine import ActorContext, DocumentStatus, WorkflowAction, evaluate_transition


def test_transition_result_allowed_contract(submitted_document, manager):
    result = evaluate_transition(
        current_status=DocumentStatus.SUBMITTED,
        action=WorkflowAction.APPROVE,
        actor=ActorContext.from_user(manager),
    )

    assert result.allowed is True
    assert result.next_status == DocumentStatus.APPROVED
    assert result.failure is None
    assert isinstance(result.reason, str)

def test_transition_result_rejected_contract(draft_document, manager):
    result = evaluate_transition(
        current_status=DocumentStatus.DRAFT,
        action=WorkflowAction.APPROVE,
        actor=ActorContext.from_user(manager),
    )

    assert result.allowed is False
    assert result.next_status is None
    assert result.failure is not None
    assert isinstance(result.reason, str)
