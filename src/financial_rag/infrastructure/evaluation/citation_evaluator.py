"""Citation quality and provenance precision evaluator."""

from financial_rag.domain.entities.evaluation import CitationEvalMetrics, EvaluationCase
from financial_rag.domain.entities.reasoning import AnswerPackage
from financial_rag.domain.interfaces.evaluation import CitationEvaluatorProtocol


class CitationEvaluator(CitationEvaluatorProtocol):
    """Evaluates citation precision, recall, validity, and claim completeness."""

    def evaluate_citations(
        self,
        answer_package: AnswerPackage,
        case: EvaluationCase,
    ) -> CitationEvalMetrics:
        """Compute citation fidelity metrics against ground truth evidence requirements."""
        citations = answer_package.citations
        if not citations:
            if case.expected_citations_count == 0:
                return CitationEvalMetrics(
                    citation_precision=1.0,
                    citation_recall=1.0,
                    citation_validity=1.0,
                    citation_completeness=1.0,
                )
            return CitationEvalMetrics(
                citation_precision=0.0,
                citation_recall=0.0,
                citation_validity=0.0,
                citation_completeness=0.0,
            )

        # 1. Validity: Are citations structurally valid and verified?
        valid_citations = sum(
            1 for c in citations if c.verified and c.page_number > 0 and len(c.source_excerpt) > 0
        )
        citation_validity = valid_citations / float(len(citations))

        # 2. Precision: Do cited citations point to expected documents/pages?
        exp_docs = set(case.expected_document_ids)
        exp_pages = set(case.expected_page_numbers)

        precise_citations = 0
        for c in citations:
            doc_ok = (
                not exp_docs
                or str(c.document_id) in exp_docs
                or any(d in str(c.document_id) for d in exp_docs)
            )
            page_ok = (
                not exp_pages
                or c.page_number in exp_pages
                or any(p in exp_pages for p in c.page_numbers)
            )
            if doc_ok and (page_ok or not exp_pages):
                precise_citations += 1

        citation_precision = precise_citations / float(len(citations))

        # 3. Recall: Did we cite all expected pages/documents?
        cited_pages = {c.page_number for c in citations}.union(
            p for c in citations for p in c.page_numbers
        )
        if exp_pages:
            covered_pages = sum(1 for p in exp_pages if p in cited_pages)
            citation_recall = covered_pages / float(len(exp_pages))
        else:
            citation_recall = min(
                1.0, float(len(citations)) / max(1, case.expected_citations_count)
            )

        # 4. Completeness: Do all generated claims have citations?
        claims = answer_package.claims
        if claims:
            claimed_citation_ids = {c.claim_id for c in citations if c.claim_id}
            cited_claims = sum(
                1
                for cl in claims
                if cl.claim_id in claimed_citation_ids or len(getattr(cl, "citation_ids", [])) > 0
            )
            citation_completeness = cited_claims / float(len(claims))
        else:
            citation_completeness = 1.0

        return CitationEvalMetrics(
            citation_precision=min(1.0, citation_precision),
            citation_recall=min(1.0, citation_recall),
            citation_validity=min(1.0, citation_validity),
            citation_completeness=min(1.0, citation_completeness),
        )
