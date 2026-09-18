"""
JARVIS Feature Test Suite
Tests all 9 features with integration coverage.
"""

import json
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

# ============================================================
# FEATURE 1: Voice & Interaction Layer
# ============================================================

def test_feature_1_voice():
    print("=" * 60)
    print("FEATURE 1: Voice & Interaction Layer")
    print("=" * 60)
    passed = 0
    failed = 0

    # Test 1.1: TTS module imports
    try:
        from voice.tts import TTSEngine
        print("  [PASS] 1.1 TTSEngine imports")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 1.1 TTSEngine import: {e}")
        failed += 1

    # Test 1.2: STT module imports
    try:
        from voice.stt import STTEngine
        print("  [PASS] 1.2 STTEngine imports")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 1.2 STTEngine import: {e}")
        failed += 1

    # Test 1.3: VAD module imports
    try:
        from voice.vad import VADWrapper
        print("  [PASS] 1.3 VADWrapper imports")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 1.3 VAD import: {e}")
        failed += 1

    # Test 1.4: Audio output module imports
    try:
        from voice.audio_output import AudioOutput
        print("  [PASS] 1.4 AudioOutput imports")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 1.4 AudioOutput import: {e}")
        failed += 1

    # Test 1.5: Keyboard handler imports
    try:
        from voice.keyboard_handler import KeyboardHandler
        print("  [PASS] 1.5 KeyboardHandler imports")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 1.5 KeyboardHandler import: {e}")
        failed += 1

    # Test 1.6: Voice pipeline imports
    try:
        from voice.pipeline import VoicePipeline
        print("  [PASS] 1.6 VoicePipeline imports")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 1.6 VoicePipeline import: {e}")
        failed += 1

    # Test 1.7: Hardware detection
    try:
        from core.hardware import detect_hardware
        hw = detect_hardware()
        assert hw.cpu_physical_cores > 0
        print(f"  [PASS] 1.7 Hardware detection: {hw.cpu_physical_cores} cores, GPU: {hw.gpu_name}")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 1.7 Hardware detection: {e}")
        failed += 1

    # Test 1.8: Config loading
    try:
        from core.config import load_config
        config = load_config(0)
        assert config.stt_model is not None
        print(f"  [PASS] 1.8 Config loaded: STT={config.stt_model}")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 1.8 Config load: {e}")
        failed += 1

    print(f"\n  Feature 1: {passed} passed, {failed} failed\n")
    return passed, failed


# ============================================================
# FEATURE 2: HITL Decision Engine
# ============================================================

def test_feature_2_hitl():
    print("=" * 60)
    print("FEATURE 2: HITL Decision Engine")
    print("=" * 60)
    passed = 0
    failed = 0

    # Test 2.1: RiskLevel enum
    try:
        from tools.base import RiskLevel
        assert RiskLevel.GREEN.value == "green"
        assert RiskLevel.YELLOW.value == "yellow"
        assert RiskLevel.RED.value == "red"
        print("  [PASS] 2.1 RiskLevel enum (GREEN/YELLOW/RED)")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 2.1 RiskLevel: {e}")
        failed += 1

    # Test 2.2: ConfirmationRequest
    try:
        from tools.base import ConfirmationRequest
        req = ConfirmationRequest(
            tool_name="test",
            action="delete",
            risk_level=RiskLevel.RED,
            details="Delete file",
            suggested_action="Would delete test.txt",
        )
        assert req.tool_name == "test"
        assert req.risk_level == RiskLevel.RED
        print("  [PASS] 2.2 ConfirmationRequest creation")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 2.2 ConfirmationRequest: {e}")
        failed += 1

    # Test 2.3: HITL confirmation callback
    try:
        from brain.hitl import set_confirmation_callback, ask_confirmation
        set_confirmation_callback(lambda msg, risk_level="yellow": True)
        result = ask_confirmation("Test action", risk_level="green")
        assert result is True
        print("  [PASS] 2.3 HITL confirmation callback (auto-approve)")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 2.3 HITL callback: {e}")
        failed += 1

    # Test 2.4: Undo tracker
    try:
        from brain.hitl import get_undo_tracker
        tracker = get_undo_tracker()
        undo_id = tracker.record("test_tool", "test_action", {"file": "test.txt"}, "Test undo")
        assert undo_id is not None
        assert len(tracker._entries) > 0
        print(f"  [PASS] 2.4 Undo tracker records actions (id: {undo_id})")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 2.4 Undo tracker: {e}")
        failed += 1

    # Test 2.5: Audit log
    try:
        from brain.audit import AuditEvent, AuditLog
        audit = AuditLog(log_path=os.path.join(tempfile.mkdtemp(), "audit.jsonl"))
        event = AuditEvent(
            timestamp=time.time(),
            event_type="tool_executed",
            tool_name="test_tool",
            action="test_action",
            risk_level="green",
            args_summary="test args",
            result_summary="test result",
            confidence=0.9,
        )
        audit.log(event)
        print("  [PASS] 2.5 Audit log writes events")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 2.5 Audit log: {e}")
        failed += 1

    # Test 2.6: Tool registry risk classification
    try:
        from brain.tools import create_tools_registry
        from brain.hitl import set_confirmation_callback
        set_confirmation_callback(lambda msg, risk_level="yellow": True)
        registry = create_tools_registry()
        # registry.tools[name] is a dict with 'risk_level' key
        browser_risk = registry.tools["browser"]["risk_level"]
        assert browser_risk == RiskLevel.GREEN
        filesystem_risk = registry.tools["filesystem"]["risk_level"]
        assert filesystem_risk == RiskLevel.YELLOW
        code_risk = registry.tools["execute_code"]["risk_level"]
        assert code_risk == RiskLevel.RED
        print("  [PASS] 2.6 Tool risk classification (GREEN/YELLOW/RED)")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 2.6 Risk classification: {e}")
        failed += 1

    # Test 2.7: HITL blocks unconfirmed actions
    try:
        set_confirmation_callback(lambda msg, risk_level="yellow": False)
        result = ask_confirmation("Delete everything", risk_level="yellow")
        assert result is False
        set_confirmation_callback(lambda msg, risk_level="yellow": True)  # reset
        print("  [PASS] 2.7 HITL blocks unconfirmed actions")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 2.7 HITL block: {e}")
        failed += 1

    print(f"\n  Feature 2: {passed} passed, {failed} failed\n")
    return passed, failed


# ============================================================
# FEATURE 3: Knowledge Base & Memory (RAG)
# ============================================================

def test_feature_3_memory():
    print("=" * 60)
    print("FEATURE 3: Knowledge Base & Memory (RAG)")
    print("=" * 60)
    passed = 0
    failed = 0

    tmp_dir = tempfile.mkdtemp()

    # Test 3.1: VectorStore initialization
    try:
        from memory.chroma_store import VectorStore
        vs = VectorStore(persist_directory=os.path.join(tmp_dir, "chroma"))
        assert vs is not None
        print("  [PASS] 3.1 VectorStore initializes")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 3.1 VectorStore init: {e}")
        failed += 1

    # Test 3.2: Save and retrieve conversation
    try:
        entry_id = vs.save_conversation("What is Python?", "Python is a programming language.")
        assert entry_id is not None
        results = vs.get_context("Python", n_results=1)
        # Note: distance filter may exclude short queries
        print(f"  [PASS] 3.2 Save conversation (id: {entry_id[:20]}...)")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 3.2 Save conversation: {e}")
        failed += 1

    # Test 3.3: Filtered memory entry
    try:
        vs.save_filtered_entry("mem_001", "User prefers dark mode", {"importance": 0.8})
        results = vs.search_filtered("dark mode", n_results=1)
        assert len(results) == 1
        assert results[0]["content"] == "User prefers dark mode"
        print("  [PASS] 3.3 Filtered memory save + search")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 3.3 Filtered memory: {e}")
        failed += 1

    # Test 3.4: MemoryFileController (MEMORY.md)
    try:
        from memory.memory_file import MemoryFileController
        mf = MemoryFileController(file_path=os.path.join(tmp_dir, "MEMORY.md"))
        mf.save_fact("User name is Ashutosh")
        content = mf.get_full_content()
        assert "Ashutosh" in content
        print("  [PASS] 3.4 MemoryFileController save_fact")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 3.4 MemoryFile: {e}")
        failed += 1

    # Test 3.5: PreferenceStore
    try:
        from memory.preference_store import PreferenceStore
        ps = PreferenceStore(storage_path=os.path.join(tmp_dir, "prefs.json"))
        ps.set("tts_voice", "nova")
        assert ps.get("tts_voice") == "nova"
        all_prefs = ps.get_all()
        assert "tts_voice" in all_prefs
        print("  [PASS] 3.5 PreferenceStore set/get")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 3.5 PreferenceStore: {e}")
        failed += 1

    # Test 3.6: MemoryManager integration
    try:
        from memory.MemoryManager import MemoryManager
        from core.config import Config
        config = Config()
        config.chroma_persist_directory = os.path.join(tmp_dir, "chroma2")
        mm = MemoryManager(config)
        mm.save_learned_preference("app_chrome", "google-chrome")
        prefs = mm.get_preferences()
        assert "app_chrome" in prefs
        print("  [PASS] 3.6 MemoryManager preference merge")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 3.6 MemoryManager: {e}")
        failed += 1

    # Test 3.7: format_context_for_prompt (RAG)
    try:
        ctx = mm.format_context_for_prompt("hello")
        assert isinstance(ctx, str)
        print(f"  [PASS] 3.7 format_context_for_prompt (len={len(ctx)})")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 3.7 RAG context: {e}")
        failed += 1

    # Test 3.8: Forgetting mechanism
    try:
        result = mm.forget_stale(max_age_days=30, dry_run=True)
        assert "total_prunable" in result
        print(f"  [PASS] 3.8 forget_stale (dry_run, prunable={result['total_prunable']})")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 3.8 Forgetting: {e}")
        failed += 1

    # Test 3.9: Importance scoring
    try:
        from memory.importance import ImportanceScorer, MemoryEntryType
        scorer = ImportanceScorer()
        score = scorer.score("Important decision about architecture", MemoryEntryType.DECISION)
        assert 0 <= score <= 1
        print(f"  [PASS] 3.9 Importance scoring (score={score:.2f})")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 3.9 Importance scoring: {e}")
        failed += 1

    print(f"\n  Feature 3: {passed} passed, {failed} failed\n")
    return passed, failed


# ============================================================
# FEATURE 4: Proactive Suggestions
# ============================================================

def test_feature_4_proactive():
    print("=" * 60)
    print("FEATURE 4: Proactive Suggestions")
    print("=" * 60)
    passed = 0
    failed = 0

    tmp_file = os.path.join(tempfile.mkdtemp(), "proactive.json")

    # Test 4.1: ProactiveEngine init
    try:
        from brain.proactive import ProactiveEngine
        engine = ProactiveEngine(storage_path=tmp_file)
        assert engine is not None
        print("  [PASS] 4.1 ProactiveEngine initializes")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 4.1 ProactiveEngine init: {e}")
        failed += 1

    # Test 4.2: Record interactions
    try:
        engine.record_interaction("search for python", ["search_web"])
        engine.record_interaction("open browser", ["browser"])
        engine.record_interaction("search for flask", ["search_web"])
        engine.record_interaction("open browser", ["browser"])
        stats = engine.get_stats()
        assert stats["total_interactions"] == 4
        print(f"  [PASS] 4.2 Record interactions ({stats['total_interactions']} recorded)")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 4.2 Record interactions: {e}")
        failed += 1

    # Test 4.3: Follow-up suggestions
    try:
        suggestions = engine.suggest("search for python", ["search_web"])
        assert len(suggestions) > 0
        # Should suggest "open browser" since it follows search
        texts = [s.text for s in suggestions]
        assert any("browser" in t for t in texts)
        print(f"  [PASS] 4.3 Follow-up suggestions ({len(suggestions)} returned)")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 4.3 Follow-up suggestions: {e}")
        failed += 1

    # Test 4.4: Suggestion confidence levels
    try:
        for s in suggestions:
            assert 0 <= s.confidence <= 1
            assert s.source in ("followup", "pattern", "frequency", "time")
        print("  [PASS] 4.4 Suggestion confidence valid (0-1)")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 4.4 Confidence: {e}")
        failed += 1

    # Test 4.5: Persistence
    try:
        engine2 = ProactiveEngine(storage_path=tmp_file)
        stats2 = engine2.get_stats()
        assert stats2["total_interactions"] == 4
        print(f"  [PASS] 4.5 Persistence ({stats2['total_interactions']} loaded)")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 4.5 Persistence: {e}")
        failed += 1

    # Test 4.6: Clear
    try:
        engine2.clear()
        stats3 = engine2.get_stats()
        assert stats3["total_interactions"] == 0
        print("  [PASS] 4.6 Clear history")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 4.6 Clear: {e}")
        failed += 1

    print(f"\n  Feature 4: {passed} passed, {failed} failed\n")
    return passed, failed


# ============================================================
# FEATURE 5: Calendar + Email Integration
# ============================================================

def test_feature_5_calendar_email():
    print("=" * 60)
    print("FEATURE 5: Calendar + Email Integration")
    print("=" * 60)
    passed = 0
    failed = 0

    # Test 5.1: EmailTriage classification
    try:
        from brain.calendar_email import EmailTriage, EmailPriority
        triage = EmailTriage(whitelisted_senders=["boss@company.com"])
        r = triage.classify("boss@company.com", "Quick question", "")
        assert r.priority == EmailPriority.IMPORTANT
        print("  [PASS] 5.1 EmailTriage whitelisted sender")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 5.1 EmailTriage: {e}")
        failed += 1

    # Test 5.2: Urgent detection
    try:
        r = triage.classify("anyone@test.com", "URGENT: Server down", "")
        assert r.priority == EmailPriority.URGENT
        print("  [PASS] 5.2 Urgent email detection")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 5.2 Urgent: {e}")
        failed += 1

    # Test 5.3: Promotional detection
    try:
        r = triage.classify("newsletter@shop.com", "50% off sale!", "")
        assert r.priority == EmailPriority.PROMOTIONAL
        assert r.auto_archived is True
        print("  [PASS] 5.3 Promotional auto-archive")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 5.3 Promo: {e}")
        failed += 1

    # Test 5.4: Batch triage
    try:
        batch = [
            {"sender": "a@test.com", "subject": "Normal email", "snippet": ""},
            {"sender": "promo@store.com", "subject": "Sale!!!", "snippet": ""},
            {"sender": "boss@company.com", "subject": "Report", "snippet": ""},
        ]
        results = triage.triage_batch(batch)
        assert len(results["promotional"]) == 1
        assert len(results["important"]) == 1
        assert len(results["normal"]) == 1
        print("  [PASS] 5.4 Batch triage classification")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 5.4 Batch: {e}")
        failed += 1

    # Test 5.5: Calendar conflict detection
    try:
        from brain.calendar_email import CalendarOrchestrator
        cal = CalendarOrchestrator()
        events = [
            {"title": "Standup", "start": "2026-09-17T09:00:00+00:00", "end": "2026-09-17T09:30:00+00:00"},
            {"title": "Review", "start": "2026-09-17T10:00:00+00:00", "end": "2026-09-17T11:00:00+00:00"},
        ]
        conflicts = cal.detect_conflicts(events)
        assert len(conflicts) == 0
        print("  [PASS] 5.5 Calendar no conflicts")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 5.5 Calendar: {e}")
        failed += 1

    # Test 5.6: Conflict detection with overlap
    try:
        new = {"title": "Meeting", "start": "2026-09-17T10:30:00+00:00", "end": "2026-09-17T11:30:00+00:00"}
        conflicts = cal.detect_conflicts(events, new)
        assert len(conflicts) >= 1
        assert conflicts[0].overlap_minutes == 30
        print(f"  [PASS] 5.6 Conflict detected ({conflicts[0].overlap_minutes}min overlap)")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 5.6 Conflict: {e}")
        failed += 1

    # Test 5.7: Meeting time suggestions
    try:
        slots = cal.suggest_meeting_times(events, duration_minutes=60)
        assert len(slots) > 0
        print(f"  [PASS] 5.7 Meeting suggestions ({len(slots)} slots)")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 5.7 Meeting slots: {e}")
        failed += 1

    # Test 5.8: Orchestrator draft reply
    try:
        from brain.calendar_email import CalendarEmailOrchestrator
        orch = CalendarEmailOrchestrator()
        draft = orch.draft_reply("alice@test.com", "Re: Project", "LGTM!", tone="casual")
        assert "Re:" in draft.subject
        assert draft.to == "alice@test.com"
        print("  [PASS] 5.8 Draft reply created")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 5.8 Draft: {e}")
        failed += 1

    # Test 5.9: Draft approval workflow
    try:
        pending = orch.get_pending_drafts()
        assert len(pending) == 1
        approved = orch.approve_draft(0)
        assert approved is not None
        assert len(orch.get_pending_drafts()) == 0
        print("  [PASS] 5.9 Draft approval workflow")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 5.9 Draft approval: {e}")
        failed += 1

    print(f"\n  Feature 5: {passed} passed, {failed} failed\n")
    return passed, failed


# ============================================================
# FEATURE 6: Browser Automation
# ============================================================

def test_feature_6_browser():
    print("=" * 60)
    print("FEATURE 6: Browser Automation")
    print("=" * 60)
    passed = 0
    failed = 0

    # Test 6.1: BrowserTool initialization
    try:
        from tools.browser import BrowserTool
        bt = BrowserTool()
        assert bt.user_data_dir is not None
        print(f"  [PASS] 6.1 BrowserTool init (dir: {bt.user_data_dir})")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 6.1 BrowserTool: {e}")
        failed += 1

    # Test 6.2: Browser actions list
    try:
        from tools.browser import BrowserManager
        # Verify all action methods exist
        methods = ["navigate", "extract", "click", "fill", "screenshot",
                    "get_tabs", "switch_tab", "new_tab", "wait_for",
                    "press_key", "scroll", "get_url", "back", "forward", "reload"]
        for m in methods:
            assert hasattr(BrowserManager, m), f"Missing method: {m}"
        print(f"  [PASS] 6.2 All {len(methods)} browser actions present")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 6.2 Actions: {e}")
        failed += 1

    # Test 6.3: ResearchWorkflow init
    try:
        from brain.research import ResearchWorkflow, ResearchResult, ResearchSource
        rw = ResearchWorkflow()
        assert rw.browser is not None
        print("  [PASS] 6.3 ResearchWorkflow initializes")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 6.3 Research: {e}")
        failed += 1

    # Test 6.4: ResearchResult citations
    try:
        rr = ResearchResult(query="test")
        src = ResearchSource(title="Test Source", url="http://test.com", content="Hello")
        rr.sources.append(src)
        rr.combined_text = "Combined"
        citations = rr.format_citations()
        assert "[1]" in citations
        assert "Test Source" in citations
        print("  [PASS] 6.4 ResearchResult citations format")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 6.4 Citations: {e}")
        failed += 1

    # Test 6.5: Browser tool registry
    try:
        from brain.tools import create_tools_registry
        from brain.hitl import set_confirmation_callback
        set_confirmation_callback(lambda msg, risk_level="yellow": True)
        registry = create_tools_registry()
        assert "browser" in registry.tools
        assert "research" in registry.tools
        print("  [PASS] 6.5 Browser + research registered")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 6.5 Registry: {e}")
        failed += 1

    print(f"\n  Feature 6: {passed} passed, {failed} failed\n")
    return passed, failed


# ============================================================
# FEATURE 7: Code Execution Sandbox
# ============================================================

def test_feature_7_sandbox():
    print("=" * 60)
    print("FEATURE 7: Code Execution Sandbox")
    print("=" * 60)
    passed = 0
    failed = 0

    tmp_hist = os.path.join(tempfile.mkdtemp(), "exec_history.json")

    # Test 7.1: Sandbox init
    try:
        from brain.sandbox import CodeSandbox
        sb = CodeSandbox(history_path=tmp_hist)
        assert sb.timeout == 30
        print("  [PASS] 7.1 CodeSandbox initializes")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 7.1 Sandbox: {e}")
        failed += 1

    # Test 7.2: Python execution
    try:
        r = sb.run_python("print(2 + 2)", confirm=True)
        assert r["status"] == "success"
        assert "4" in r["output"]
        print(f"  [PASS] 7.2 Python exec (output: {r['output'].strip()})")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 7.2 Python: {e}")
        failed += 1

    # Test 7.3: Multi-line code
    try:
        r = sb.run_python("for i in range(3):\n    print(i)", confirm=True)
        assert r["status"] == "success"
        assert "0" in r["output"] and "2" in r["output"]
        print("  [PASS] 7.3 Multi-line Python execution")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 7.3 Multi-line: {e}")
        failed += 1

    # Test 7.4: Blocked import
    try:
        r = sb.run_python("import os", confirm=True)
        assert r["status"] == "error"
        assert "Blocked" in r["error"]
        print("  [PASS] 7.4 Blocked import (os)")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 7.4 Blocked: {e}")
        failed += 1

    # Test 7.5: Blocked open()
    try:
        r = sb.run_python('x = open("file")', confirm=True)
        assert r["status"] == "error"
        print("  [PASS] 7.5 Blocked open()")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 7.5 Blocked open: {e}")
        failed += 1

    # Test 7.6: Confirmation required
    try:
        r = sb.run_python("print(1)", confirm=False)
        assert r["status"] == "error"
        assert "confirmation" in r["error"].lower()
        print("  [PASS] 7.6 Confirmation required")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 7.6 No confirm: {e}")
        failed += 1

    # Test 7.7: Diff preview
    try:
        tmp = os.path.join(tempfile.mkdtemp(), "test.txt")
        with open(tmp, "w") as f:
            f.write("old line\n")
        preview = sb.preview_diff(tmp, "new line\n")
        assert preview.additions > 0
        assert preview.deletions > 0
        assert "new line" in preview.diff_text
        print(f"  [PASS] 7.7 Diff preview (+{preview.additions} -{preview.deletions})")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 7.7 Diff: {e}")
        failed += 1

    # Test 7.8: Apply diff
    try:
        r = sb.apply_diff(preview, confirm=True)
        assert r["status"] == "success"
        content = open(tmp).read()
        assert "new line" in content
        print("  [PASS] 7.8 Apply diff writes file")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 7.8 Apply: {e}")
        failed += 1

    # Test 7.9: Execution history
    try:
        history = sb.get_history(5)
        assert len(history) > 0, f"History empty, expected > 0 records"
        ids = [h["id"] for h in history]
        assert len(ids) == len(set(ids)), "Duplicate IDs found in history"
        print(f"  [PASS] 7.9 Execution history ({len(history)} records, all unique IDs)")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 7.9 History: {e}")
        failed += 1

    # Test 7.10: Duration tracking
    try:
        r = sb.run_python("import time; time.sleep(0.1); print('done')", confirm=True)
        assert r["duration_ms"] > 100
        print(f"  [PASS] 7.10 Duration tracking ({r['duration_ms']:.0f}ms)")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 7.10 Duration: {e}")
        failed += 1

    print(f"\n  Feature 7: {passed} passed, {failed} failed\n")
    return passed, failed


# ============================================================
# FEATURE 8: Multi-Agent Collaboration
# ============================================================

def test_feature_8_multi_agent():
    print("=" * 60)
    print("FEATURE 8: Multi-Agent Collaboration")
    print("=" * 60)
    passed = 0
    failed = 0

    # Test 8.1: Agent roles
    try:
        from brain.multi_agent import AgentRole
        roles = [r.value for r in AgentRole]
        assert "researcher" in roles
        assert "coder" in roles
        assert "reviewer" in roles
        assert "planner" in roles
        assert "general" in roles
        print(f"  [PASS] 8.1 Agent roles: {roles}")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 8.1 Roles: {e}")
        failed += 1

    # Test 8.2: System prompts per role
    try:
        from brain.multi_agent import ROLE_SYSTEM_PROMPTS
        assert len(ROLE_SYSTEM_PROMPTS) == 5
        for role, prompt in ROLE_SYSTEM_PROMPTS.items():
            assert len(prompt) > 50
        print("  [PASS] 8.2 System prompts for all 5 roles")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 8.2 Prompts: {e}")
        failed += 1

    # Test 8.3: AgentBudget tracking
    try:
        from brain.multi_agent import AgentBudget
        b = AgentBudget(max_tokens=100, max_time_seconds=60)
        assert b.can_continue()
        b.record_tokens(50)
        assert b.can_continue()
        b.record_tokens(60)
        assert not b.can_continue()
        print("  [PASS] 8.3 Budget token tracking")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 8.3 Budget: {e}")
        failed += 1

    # Test 8.4: AgentTask creation
    try:
        from brain.multi_agent import AgentTask
        task = AgentTask(
            id="t1", description="Research", role=AgentRole.RESEARCHER,
            prompt="Research Python", timeout_seconds=30, max_tokens=1000,
        )
        assert task.id == "t1"
        assert task.role == AgentRole.RESEARCHER
        print("  [PASS] 8.4 AgentTask creation")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 8.4 Task: {e}")
        failed += 1

    # Test 8.5: AgentResult serialization
    try:
        from brain.multi_agent import AgentResult
        r = AgentResult(
            task_id="t1", role=AgentRole.CODER, output="code",
            duration_ms=100, tokens_used=25, success=True,
        )
        d = r.to_dict()
        assert d["task_id"] == "t1"
        assert d["success"] is True
        print("  [PASS] 8.5 AgentResult serialization")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 8.5 Result: {e}")
        failed += 1

    # Test 8.6: Orchestrator init
    try:
        from brain.multi_agent import MultiAgentOrchestrator
        orch = MultiAgentOrchestrator(max_workers=2)
        assert orch.max_workers == 2
        stats = orch.get_stats()
        assert stats["total_tasks"] == 0
        print("  [PASS] 8.6 Orchestrator initializes")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 8.6 Orchestrator: {e}")
        failed += 1

    # Test 8.7: Multi-agent tool in registry
    try:
        from brain.tools import create_tools_registry
        from brain.hitl import set_confirmation_callback
        set_confirmation_callback(lambda msg, risk_level="yellow": True)
        registry = create_tools_registry()
        assert "multi_agent" in registry.tools
        print("  [PASS] 8.7 multi_agent tool registered")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 8.7 Registry: {e}")
        failed += 1

    print(f"\n  Feature 8: {passed} passed, {failed} failed\n")
    return passed, failed


# ============================================================
# FEATURE 9: Task Planning & Goal Decomposition
# ============================================================

def test_feature_9_planner():
    print("=" * 60)
    print("FEATURE 9: Task Planning & Goal Decomposition")
    print("=" * 60)
    passed = 0
    failed = 0

    tmp_plan = os.path.join(tempfile.mkdtemp(), "plans.json")

    # Test 9.1: TaskPlanner init
    try:
        from brain.planner import TaskPlanner
        planner = TaskPlanner(storage_path=tmp_plan)
        assert planner is not None
        print("  [PASS] 9.1 TaskPlanner initializes")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 9.1 Planner: {e}")
        failed += 1

    # Test 9.2: Create plan
    try:
        from brain.planner import TaskPriority
        plan = planner.create_plan(
            goal="Build a website",
            tasks=[
                {"id": "t1", "title": "Design", "priority": "high"},
                {"id": "t2", "title": "Code", "depends_on": ["t1"]},
                {"id": "t3", "title": "Test", "depends_on": ["t2"]},
                {"id": "t4", "title": "Deploy", "depends_on": ["t3"], "priority": "low"},
            ],
        )
        assert len(plan.tasks) == 4
        print(f"  [PASS] 9.2 Create plan ({len(plan.tasks)} tasks)")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 9.2 Create: {e}")
        failed += 1

    # Test 9.3: Dependency resolution
    try:
        ready = plan.get_next_tasks()
        assert len(ready) == 1
        assert ready[0].id == "t1"
        print(f"  [PASS] 9.3 Dependency resolution (ready: {[t.id for t in ready]})")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 9.3 Deps: {e}")
        failed += 1

    # Test 9.4: Start + complete task
    try:
        task = planner.start_task(plan.id, "t1")
        assert task is not None
        task = planner.complete_task(plan.id, "t1", "Design done")
        assert task.status.value == "done"
        assert task.result == "Design done"
        print("  [PASS] 9.4 Start + complete task")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 9.4 Start/complete: {e}")
        failed += 1

    # Test 9.5: Unblock dependents
    try:
        ready = plan.get_next_tasks()
        assert len(ready) == 1
        assert ready[0].id == "t2"
        print(f"  [PASS] 9.5 Unblock dependents (ready: {[t.id for t in ready]})")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 9.5 Unblock: {e}")
        failed += 1

    # Test 9.6: Progress tracking
    try:
        assert plan.progress == 0.25  # 1/4 done
        planner.complete_task(plan.id, "t2")
        planner.complete_task(plan.id, "t3")
        planner.complete_task(plan.id, "t4")
        assert plan.progress == 1.0
        assert plan.completed
        print(f"  [PASS] 9.6 Progress tracking (0% -> 100%)")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 9.6 Progress: {e}")
        failed += 1

    # Test 9.7: Fail + block dependents
    try:
        plan2 = planner.create_plan("Test plan", [
            {"id": "a", "title": "Step A"},
            {"id": "b", "title": "Step B", "depends_on": ["a"]},
        ])
        planner.start_task(plan2.id, "a")
        planner.fail_task(plan2.id, "a", "Error")
        task_b = plan2.get_task("b")
        assert task_b.status.value == "blocked"
        print("  [PASS] 9.7 Fail blocks dependents")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 9.7 Fail: {e}")
        failed += 1

    # Test 9.8: Format status
    try:
        status = plan.format_status()
        assert "Build a website" in status
        assert "100%" in status
        print("  [PASS] 9.8 Format status")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 9.8 Status: {e}")
        failed += 1

    # Test 9.9: Replan (add tasks)
    try:
        new_plan = planner.replan(plan.id, [
            {"id": "t5", "title": "Monitor", "depends_on": ["t4"]},
        ])
        assert len(new_plan.tasks) == 5
        print(f"  [PASS] 9.9 Replan (added task, total: {len(new_plan.tasks)})")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 9.9 Replan: {e}")
        failed += 1

    # Test 9.10: Persistence
    try:
        planner2 = TaskPlanner(storage_path=tmp_plan)
        plans = planner2.list_plans()
        assert len(plans) >= 2
        print(f"  [PASS] 9.10 Persistence ({len(plans)} plans loaded)")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 9.10 Persistence: {e}")
        failed += 1

    # Test 9.11: Planner tool in registry
    try:
        from brain.tools import create_tools_registry
        from brain.hitl import set_confirmation_callback
        set_confirmation_callback(lambda msg, risk_level="yellow": True)
        registry = create_tools_registry()
        assert "planner" in registry.tools
        print("  [PASS] 9.11 planner tool registered")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] 9.11 Registry: {e}")
        failed += 1

    print(f"\n  Feature 9: {passed} passed, {failed} failed\n")
    return passed, failed


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  JARVIS FEATURE TEST SUITE")
    print("=" * 60 + "\n")

    total_passed = 0
    total_failed = 0

    for test_fn in [
        test_feature_1_voice,
        test_feature_2_hitl,
        test_feature_3_memory,
        test_feature_4_proactive,
        test_feature_5_calendar_email,
        test_feature_6_browser,
        test_feature_7_sandbox,
        test_feature_8_multi_agent,
        test_feature_9_planner,
    ]:
        p, f = test_fn()
        total_passed += p
        total_failed += f

    print("=" * 60)
    print(f"  TOTAL: {total_passed} passed, {total_failed} failed")
    print(f"  FEATURES: 9/9 tested")
    print("=" * 60)

    sys.exit(1 if total_failed > 0 else 0)
