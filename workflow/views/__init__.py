from .document_update import DocumentUpdateView
from .document_review_list import ApprovalQueueListView
from .document_decision import DocumentApproveView, DocumentRejectView
from .login_redirect import RoleBasedLoginView
from .document_audit import DocumentAuditLogView
from .document_list import DocumentListView
from .document_detail import DocumentDetailView
from .document_submit import DocumentSubmitView
from .home import home
from .dashboard import DashboardView