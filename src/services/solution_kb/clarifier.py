"""KB-driven clarification question generation.

Goal: when user description is incomplete, ask the minimum number of high-signal
questions that best disambiguate between mature solution templates.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from ...models.user_requirement import RequirementType, UserRequirement
from ..solution_kb.retriever import SolutionTemplateRetriever
from ..solution_kb.models import TemplateExtract


@dataclass(frozen=True)
class ClarificationPlan:
    needs_clarification: bool
    questions: List[str]
    assumptions: List[str]
    candidate_templates: List[TemplateExtract]


class KBClarificationService:
    """Builds clarification questions based on KB candidate-template differences."""

    def __init__(self, retriever: Optional[SolutionTemplateRetriever] = None):
        self.retriever = retriever or SolutionTemplateRetriever()

    def plan(self, requirements: List[UserRequirement], *, limit: int = 4) -> ClarificationPlan:
        missing = self._missing_requirement_types(requirements)
        candidates = [rt.template for rt in self.retriever.retrieve(requirements, limit=6)]
        # If keyword retrieval yields no candidates but KB has data, fall back to a small sample.
        # This keeps clarification useful even when the user description is very sparse or uses
        # synonyms not present in tags/metadata yet.
        if not candidates and hasattr(self.retriever, "store") and hasattr(self.retriever.store, "list_all"):
            try:
                candidates = list(self.retriever.store.list_all())[:6]
            except Exception:
                candidates = []

        questions: List[str] = []
        assumptions: List[str] = []

        # 1) Ask for missing core info first (minimal, multiple-choice style).
        if RequirementType.APPLICATION_TYPE in missing:
            questions.append("您的应用类型是什么？（Web/API/移动后端/数据分析/批处理/IoT/其他）")
        if RequirementType.SCALE in missing:
            questions.append("大概规模是多少？（并发用户/峰值QPS/日活/数据量，给一个区间也可以）")
        if RequirementType.CONSTRAINT in missing:
            questions.append("最重要的约束是什么？（高可用/安全合规/低延迟/成本优化/可扩展性）可多选")
        if RequirementType.PREFERENCE in missing:
            questions.append("有偏好吗？（Region、是否Serverless优先、是否必须私网/VPC、是否容器化）")

        # 2) If we have candidates, ask discriminative questions driven by differences.
        if candidates:
            diff_qs = self._questions_from_candidate_differences(candidates)
            for q in diff_qs:
                if q not in questions:
                    questions.append(q)

        # Keep to the requested limit.
        questions = questions[:limit]

        # Determine if clarification is needed.
        needs = bool(questions) and (
            RequirementType.APPLICATION_TYPE in missing
            or RequirementType.SCALE in missing
            or (len(candidates) >= 2 and len(self._questions_from_candidate_differences(candidates)) > 0)
        )

        # Default assumptions to be transparent if user skips details.
        if needs:
            assumptions.append("若您暂时不确定，我会先按“生产环境 + 多可用区/高可用 + 基础安全（最小权限/加密）”的默认假设给出方案。")

        return ClarificationPlan(
            needs_clarification=needs,
            questions=questions,
            assumptions=assumptions,
            candidate_templates=candidates,
        )

    def _missing_requirement_types(self, requirements: List[UserRequirement]) -> Set[RequirementType]:
        present = {r.requirement_type for r in requirements if r.requirement_value and r.confidence >= 0.5}
        return {
            RequirementType.APPLICATION_TYPE,
            RequirementType.SCALE,
            RequirementType.CONSTRAINT,
            RequirementType.PREFERENCE,
        }.difference(present)

    def _questions_from_candidate_differences(self, candidates: List[TemplateExtract]) -> List[str]:
        # Build feature flags per candidate.
        flags = [self._infer_features(set(t.resource_types)) for t in candidates]
        if not flags:
            return []

        n = len(flags)
        # For each feature, if mixed presence across candidates => discriminative.
        mixed: List[Tuple[str, int]] = []
        all_keys = set().union(*[set(f.keys()) for f in flags])
        for k in all_keys:
            cnt = sum(1 for f in flags if f.get(k, False))
            if 0 < cnt < n:
                mixed.append((k, cnt))
        mixed.sort(key=lambda x: abs(n / 2 - x[1]))  # prefer closest to half split

        qs: List[str] = []
        for k, _ in mixed:
            q = self._feature_to_question(k)
            if q:
                qs.append(q)
        return qs

    def _infer_features(self, resource_types: Set[str]) -> Dict[str, bool]:
        def has(prefix: str) -> bool:
            return any(rt.startswith(prefix) for rt in resource_types)

        def has_exact(t: str) -> bool:
            return t in resource_types

        features: Dict[str, bool] = {
            # compute
            "compute_serverless": has_exact("AWS::Lambda::Function"),
            "compute_ec2": has_exact("AWS::EC2::Instance") or has_exact("AWS::AutoScaling::AutoScalingGroup"),
            "compute_containers": has_exact("AWS::ECS::Service") or has_exact("AWS::EKS::Cluster"),
            # data
            "db_relational": has("AWS::RDS::"),
            "db_nosql": has_exact("AWS::DynamoDB::Table"),
            "cache": has("AWS::ElastiCache::"),
            # edge/api
            "api_gateway": has("AWS::ApiGateway::") or has("AWS::ApiGatewayV2::"),
            "cdn": has_exact("AWS::CloudFront::Distribution"),
            # security
            "waf": has("AWS::WAFv2::") or has("AWS::WAF::"),
            "kms": has_exact("AWS::KMS::Key"),
            # networking
            "vpc": has_exact("AWS::EC2::VPC") or has_exact("AWS::EC2::Subnet"),
            "load_balancer": has_exact("AWS::ElasticLoadBalancingV2::LoadBalancer"),
            # messaging
            "queue": has_exact("AWS::SQS::Queue"),
            "topic": has_exact("AWS::SNS::Topic"),
        }
        return features

    def _feature_to_question(self, feature: str) -> Optional[str]:
        mapping = {
            "compute_serverless": "是否优先选择 Serverless（如 Lambda）？还是接受容器/EC2？",
            "compute_containers": "是否需要容器化部署（ECS/EKS）？还是更偏向 Serverless/EC2？",
            "compute_ec2": "是否可以使用 EC2/ASG 这类自管计算？还是希望尽量托管（Serverless/托管容器）？",
            "db_relational": "数据层更偏向关系型数据库（RDS/Aurora）还是 NoSQL（DynamoDB）？",
            "db_nosql": "是否需要事务/复杂查询（更像RDS）？还是Key-Value/高扩展（更像DynamoDB）？",
            "waf": "是否需要 Web 防护（WAF/防爬/防注入）？",
            "cdn": "是否需要 CDN/加速（CloudFront）来优化静态资源或全球访问？",
            "kms": "是否有合规要求需要 KMS 管理密钥/强制加密？",
            "vpc": "是否必须部署在私有网络（VPC/内网）中？",
            "load_balancer": "入口是否需要负载均衡（ALB/NLB）？",
            "api_gateway": "对外接口是否主要是 API（需要 API Gateway）？",
            "cache": "是否需要缓存层（Redis/ElastiCache）来减轻数据库压力？",
            "queue": "是否需要异步解耦（SQS 等队列）？",
            "topic": "是否需要事件广播/发布订阅（SNS）？",
        }
        return mapping.get(feature)

