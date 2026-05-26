import asyncio
import sys
sys.path.insert(0, '/app/legiongasper_framework_0813')

from legiongasper.core.captain import Captain
from legiongasper.core.factory import AgentFactory
from legiongasper.core.squad import Squad
from legiongasper.config.captain_roles import CodeReviewer

SAMPLE_CODE = 

async def code_review_demo():
    
    print("=" * 60)
    print("⚡ LEGIONGASPER Code Review Captain Demo")
    print("=" * 60)
    print()
    
    factory = AgentFactory()
    
    print("[1] Spawning Code Review Captain...")
    captain = Captain(
        agent_id="code_review_lead",
        role=CodeReviewer(),
        llm_config={"model_tier": "balanced"}
    )
    print(f"    ✓ Captain spawned: {captain.agent_id}")
    print()
    
    print("[2] Code to Review:")
    print("-" * 60)
    print(SAMPLE_CODE)
    print("-" * 60)
    print()
    
    print("[3] Captain decomposing review into specialized areas...")
    review_areas = [
        {
            "description": "Security Review: Check for vulnerabilities, injection risks, unsafe eval",
            "focus": "security",
            "priority": "high"
        },
        {
            "description": "Style Review: Check PEP8 compliance, naming conventions, documentation",
            "focus": "style",
            "priority": "medium"
        },
        {
            "description": "Performance Review: Check algorithm efficiency, resource usage, optimization opportunities",
            "focus": "performance",
            "priority": "medium"
        },
        {
            "description": "Logic Review: Check business logic correctness, edge cases, error handling",
            "focus": "logic",
            "priority": "high"
        }
    ]
    
    print(f"    Review areas identified:")
    for i, area in enumerate(review_areas, 1):
        print(f"      {i}. {area['focus'].upper()} - {area['description'][:50]}...")
    print()
    
    print("[4] Forming code review squad...")
    
    security_agent = await factory.spawn(
        template_id="security_reviewer",
        agent_id="security_specialist"
    )
    style_agent = await factory.spawn(
        template_id="style_reviewer",
        agent_id="style_specialist"
    )
    perf_agent = await factory.spawn(
        template_id="performance_reviewer",
        agent_id="performance_specialist"
    )
    logic_agent = await factory.spawn(
        template_id="logic_reviewer",
        agent_id="logic_specialist"
    )
    
    squad = Squad(
        squad_id="code_review_squad",
        max_concurrent=4
    )
    squad.add_agent(security_agent)
    squad.add_agent(style_agent)
    squad.add_agent(perf_agent)
    squad.add_agent(logic_agent)
    
    print(f"    ✓ Review squad formed with {len(squad.agents)} specialists")
    print()
    
    print("[5] Review Squad:")
    for agent in squad.agents:
        print(f"    - {agent.agent_id}")
    print()
    
    print("[6] Executing parallel code reviews...")
    print("    (Simulating review execution)")
    
    mock_reviews = [
        {
            "agent_id": "security_specialist",
            "focus": "security",
            "issues": [
                {
                    "severity": "critical",
                    "line": 4,
                    "message": "Use of eval() is dangerous and allows code injection",
                    "suggestion": "Use ast.literal_eval() or json.loads() instead"
                },
                {
                    "severity": "medium",
                    "line": 8,
                    "message": "No input validation before processing",
                    "suggestion": "Add validation for data structure and types"
                }
            ],
            "score": 3.5,
            "confidence": 0.95
        },
        {
            "agent_id": "style_specialist",
            "focus": "style",
            "issues": [
                {
                    "severity": "low",
                    "line": 1,
                    "message": "Function missing docstring",
                    "suggestion": "Add docstring describing function purpose and parameters"
                },
                {
                    "severity": "low",
                    "line": 4,
                    "message": "TODO comment should be addressed",
                    "suggestion": "Implement validation or remove TODO"
                }
            ],
            "score": 7.0,
            "confidence": 0.90
        },
        {
            "agent_id": "performance_specialist",
            "focus": "performance",
            "issues": [
                {
                    "severity": "medium",
                    "line": 13,
                    "message": "Loop could be optimized with sum() and generator",
                    "suggestion": "Use sum(item['price'] * item['quantity'] for item in items)"
                }
            ],
            "score": 8.0,
            "confidence": 0.92
        },
        {
            "agent_id": "logic_specialist",
            "focus": "logic",
            "issues": [
                {
                    "severity": "high",
                    "line": 4,
                    "message": "eval() may raise exceptions on invalid input",
                    "suggestion": "Wrap in try-except block or use safer parsing"
                },
                {
                    "severity": "medium",
                    "line": 13,
                    "message": "No check for missing keys in items",
                    "suggestion": "Use .get() with defaults or validate schema"
                }
            ],
            "score": 6.0,
            "confidence": 0.88
        }
    ]
    
    await asyncio.sleep(1.5)
    print("    ✓ All reviews completed")
    print()
    
    print("[7] Captain aggregating review results...")
    
    total_issues = sum(len(r["issues"]) for r in mock_reviews)
    critical_issues = sum(
        1 for r in mock_reviews for i in r["issues"] if i["severity"] == "critical"
    )
    avg_score = sum(r["score"] for r in mock_reviews) / len(mock_reviews)
    
    print(f"    Total issues found: {total_issues}")
    print(f"    Critical issues: {critical_issues}")
    print(f"    Average code score: {avg_score:.1f}/10")
    print()
    
    print("=" * 60)
    print("📋 CODE REVIEW REPORT")
    print("=" * 60)
    print(f"Review ID: CR-{asyncio.get_event_loop().time():.0f}")
    print(f"Lead Reviewer: {captain.agent_id}")
    print(f"Reviewers: {len(squad.agents)} specialists")
    print(f"Overall Score: {avg_score:.1f}/10")
    print("-" * 60)
    print()
    
    print("🔒 SECURITY REVIEW")
    print("-" * 40)
    security_review = next(r for r in mock_reviews if r["focus"] == "security")
    for issue in security_review["issues"]:
        emoji = "🔴" if issue["severity"] == "critical" else "🟡" if issue["severity"] == "medium" else "🟢"
        print(f"{emoji} Line {issue['line']}: {issue['message']}")
        print(f"   Suggestion: {issue['suggestion']}")
        print()
    
    print("📝 STYLE REVIEW")
    print("-" * 40)
    style_review = next(r for r in mock_reviews if r["focus"] == "style")
    for issue in style_review["issues"]:
        print(f"• Line {issue['line']}: {issue['message']}")
    print()
    
    print("⚡ PERFORMANCE REVIEW")
    print("-" * 40)
    perf_review = next(r for r in mock_reviews if r["focus"] == "performance")
    for issue in perf_review["issues"]:
        print(f"• Line {issue['line']}: {issue['message']}")
        print(f"  → {issue['suggestion']}")
    print()
    
    print("🧠 LOGIC REVIEW")
    print("-" * 40)
    logic_review = next(r for r in mock_reviews if r["focus"] == "logic")
    for issue in logic_review["issues"]:
        emoji = "🔴" if issue["severity"] == "high" else "🟡"
        print(f"{emoji} Line {issue['line']}: {issue['message']}")
    print()
    
    print("=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"Code Quality Score: {avg_score:.1f}/10")
    print(f"Issues by Severity:")
    print(f"  🔴 Critical: {critical_issues}")
    print(f"  🟡 Medium: {sum(1 for r in mock_reviews for i in r['issues'] if i['severity'] == 'medium')}")
    print(f"  🟢 Low: {sum(1 for r in mock_reviews for i in r['issues'] if i['severity'] == 'low')}")
    print()
    print("🎯 RECOMMENDATIONS:")
    print("  1. IMMEDIATE: Replace eval() with ast.literal_eval()")
    print("  2. Add input validation before processing")
    print("  3. Add error handling for missing dictionary keys")
    print("  4. Add docstrings to all functions")
    print("  5. Optimize calculation loop with generator expression")
    print()
    
    if avg_score >= 8.0:
        decision = "✅ APPROVED"
    elif avg_score >= 6.0:
        decision = "⚠️ APPROVED WITH CHANGES"
    else:
        decision = "❌ CHANGES REQUIRED"
    
    print(f"Final Decision: {decision}")
    print()
    print("=" * 60)
    print("✓ Code Review Demo Complete")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(code_review_demo())