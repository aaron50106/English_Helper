"use strict";

// ==================== 共用工具 ====================
async function apiPost(url, body) {
    const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body || {}),
    });
    return res.json();
}

async function apiGet(url) {
    const res = await fetch(url);
    return res.json();
}

const $ = (id) => document.getElementById(id);
const letter = (i) => String.fromCharCode(65 + i);

// ==================== 分頁切換 ====================
document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
        document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
        btn.classList.add("active");
        const tab = btn.dataset.tab;
        $("tab-" + tab).classList.add("active");
        if (tab === "records") loadRecords();
        if (tab === "add") loadCustomTable();
        if (tab === "vocab") refreshVocabStats();
    });
});

// ==================== 模組1：單字訓練 ====================
let vocabAutoTimer = null;

function vocabMode() {
    const el = document.querySelector('input[name="vocab-mode"]:checked');
    return el ? el.value : "mixed";
}

async function refreshVocabStats() {
    const s = await apiGet("/api/vocab/stats");
    $("vocab-daily").textContent =
        `今日單字訓練：已作答 ${s.answered} 題，答對 ${s.correct} 題，答錯 ${s.wrong} 題`;
}

async function loadVocabQuestion() {
    clearTimeout(vocabAutoTimer);
    const data = await apiPost("/api/vocab/question", { mode: vocabMode() });
    if (!data.ok) { alert(data.message || "出題失敗"); return; }

    $("vocab-question").textContent = data.prompt;
    $("vocab-hint").textContent = data.hint || "";
    $("vocab-feedback").textContent = "";
    $("vocab-feedback").className = "feedback";
    $("vocab-next").disabled = true;

    const box = $("vocab-options");
    box.innerHTML = "";
    data.options.forEach((opt, i) => {
        const btn = document.createElement("button");
        btn.className = "option-btn";
        btn.textContent = `${letter(i)})  ${opt}`;
        btn.dataset.letter = letter(i);
        btn.addEventListener("click", () => vocabAnswer(letter(i), btn));
        box.appendChild(btn);
    });
}

async function vocabAnswer(option, btn) {
    const buttons = [...$("vocab-options").children];
    buttons.forEach((b) => (b.disabled = true));

    const data = await apiPost("/api/vocab/answer", { option });
    const fb = $("vocab-feedback");

    if (data.is_correct) {
        btn.classList.add("correct");
        fb.textContent = "✓ 正確！";
        fb.className = "feedback ok";
        vocabAutoTimer = setTimeout(loadVocabQuestion, 500);
    } else {
        btn.classList.add("wrong");
        const correctBtn = buttons.find((b) => b.dataset.letter === data.correct_option);
        if (correctBtn) correctBtn.classList.add("correct");
        if (data.mode === "ch2en") {
            fb.textContent = `✗ 錯誤！　${data.correct_answer} : ${data.prompt}`;
        } else {
            fb.textContent = `✗ 錯誤！　${data.prompt} : ${data.correct_answer}`;
        }
        fb.className = "feedback err";
        $("vocab-next").disabled = false;
    }
    if (data.stats) {
        $("vocab-daily").textContent =
            `今日單字訓練：已作答 ${data.stats.answered} 題，答對 ${data.stats.correct} 題，答錯 ${data.stats.wrong} 題`;
    }
}

$("vocab-start").addEventListener("click", loadVocabQuestion);
$("vocab-next").addEventListener("click", loadVocabQuestion);

// ==================== 模組2：歷屆題目練習 ====================
function renderExamQuestion(data) {
    $("exam-question").textContent =
        `【${data.year}年 ${data.question_type}】\n\n${data.prompt}`;
    $("exam-feedback").textContent = "";
    $("exam-feedback").className = "feedback";
    $("exam-next").disabled = true;

    const box = $("exam-options");
    box.innerHTML = "";
    ["A", "B", "C", "D"].forEach((key) => {
        const text = data.options[key];
        const btn = document.createElement("button");
        btn.className = "option-btn";
        btn.dataset.letter = key;
        if (text) {
            btn.textContent = `${key})  ${text}`;
            btn.addEventListener("click", () => examAnswer(key, btn));
        } else {
            btn.textContent = `${key})`;
            btn.disabled = true;
        }
        box.appendChild(btn);
    });
    updateExamProgress(data.answered, data.correct, data.total);
}

function updateExamProgress(answered, correct, total) {
    const pct = total ? (answered / total) * 100 : 0;
    $("exam-bar").style.width = pct + "%";
    $("exam-score").textContent = `目前成績：${correct}/${answered} | 進度：${answered}/${total}`;
}

async function examStart() {
    const data = await apiPost("/api/exam/start", {
        year: parseInt($("exam-year").value, 10),
        type: $("exam-type").value,
        random_order: $("exam-random").checked,
    });
    if (!data.ok) { alert(data.message || "沒有符合條件的題目"); return; }
    renderExamQuestion(data);
}

async function examAnswer(option, btn) {
    [...$("exam-options").children].forEach((b) => (b.disabled = true));
    const data = await apiPost("/api/exam/answer", { option });
    const fb = $("exam-feedback");

    if (data.has_answer) {
        if (data.is_correct) {
            btn.classList.add("correct");
            fb.textContent = "✓ 正確！";
            fb.className = "feedback ok";
        } else {
            btn.classList.add("wrong");
            const c = [...$("exam-options").children].find((b) => b.dataset.letter === data.correct_option);
            if (c) c.classList.add("correct");
            fb.textContent = `✗ 錯誤！正確答案是 ${data.correct_option}`;
            fb.className = "feedback err";
        }
    } else {
        fb.textContent = `你的答案：${option}（此題暫無官方答案）`;
        fb.className = "feedback hint";
    }
    updateExamProgress(data.answered, data.correct, data.total);
    $("exam-next").disabled = false;
}

async function examNext() {
    const data = await apiPost("/api/exam/next", {});
    if (data.finished) {
        $("exam-question").textContent = "本輪練習已完成";
        const fb = $("exam-feedback");
        fb.textContent = `成績：${data.correct}/${data.total}，正確率：${data.accuracy.toFixed(1)}%`;
        fb.className = "feedback ok";
        $("exam-options").innerHTML = "";
        $("exam-next").disabled = true;
        $("exam-bar").style.width = "100%";
        $("exam-score").textContent = `目前成績：${data.correct}/${data.total} | 進度：${data.total}/${data.total}`;
        alert(`本輪練習完成。\n\n總題數：${data.total}\n正確：${data.correct}\n正確率：${data.accuracy.toFixed(1)}%`);
        return;
    }
    renderExamQuestion(data);
}

$("exam-start").addEventListener("click", examStart);
$("exam-next").addEventListener("click", examNext);

// ==================== 模組3：隨機測驗 ====================
let quizStarted = false;
let quizAutoTimer = null;

function setQuizSettings(enabled) {
    $("quiz-count").disabled = !enabled;
    $("quiz-vocab").disabled = !enabled;
    $("quiz-exam").disabled = !enabled;
    $("quiz-start").disabled = !enabled;
    $("quiz-reset").disabled = enabled;
}

function renderQuizQuestion(data) {
    $("quiz-question").textContent = data.prompt;
    $("quiz-feedback").textContent = "";
    $("quiz-feedback").className = "feedback";
    $("quiz-next").disabled = true;

    const box = $("quiz-options");
    box.innerHTML = "";
    data.options.forEach((opt, i) => {
        const btn = document.createElement("button");
        btn.className = "option-btn";
        btn.dataset.letter = letter(i);
        btn.textContent = `${letter(i)})  ${opt}`;
        btn.addEventListener("click", () => quizAnswer(letter(i), btn));
        box.appendChild(btn);
    });
    updateQuizProgress(data.answered, data.total, data.correct, data.accuracy);
}

function updateQuizProgress(answered, total, correct, accuracy) {
    const pct = total ? (answered / total) * 100 : 0;
    $("quiz-bar").style.width = pct + "%";
    $("quiz-score").textContent = `目前成績：${correct}/${answered}`;
    $("quiz-stats").textContent = `進度：${answered}/${total} | 正確率：${(accuracy || 0).toFixed(1)}%`;
}

async function quizStart() {
    if (!$("quiz-vocab").checked && !$("quiz-exam").checked) {
        alert("至少選擇一種題型");
        return;
    }
    const data = await apiPost("/api/quiz/start", {
        count: parseInt($("quiz-count").value, 10),
        include_vocab: $("quiz-vocab").checked,
        include_exam: $("quiz-exam").checked,
    });
    if (!data.ok) { alert(data.message || "無法開始測驗"); return; }
    quizStarted = true;
    setQuizSettings(false);
    if (data.finished) { await quizEnd(); return; }
    renderQuizQuestion(data);
}

async function quizAnswer(option, btn) {
    [...$("quiz-options").children].forEach((b) => (b.disabled = true));
    const data = await apiPost("/api/quiz/answer", { option });
    const fb = $("quiz-feedback");
    const s = data.stats || {};
    updateQuizProgress(s.answered, s.total_questions, s.correct, s.accuracy);

    if (data.is_correct) {
        btn.classList.add("correct");
        fb.textContent = "✓ 正確！";
        fb.className = "feedback ok";
        quizAutoTimer = setTimeout(quizAdvance, 500);
    } else {
        btn.classList.add("wrong");
        if (data.has_answer) {
            const c = [...$("quiz-options").children].find((b) => b.dataset.letter === data.correct_option);
            if (c) c.classList.add("correct");
        }
        if (data.mode === "ch2en") {
            fb.textContent = `✗ 錯誤！　${data.correct_answer} : ${data.prompt}`;
        } else if (data.mode === "en2ch") {
            fb.textContent = `✗ 錯誤！　${data.prompt} : ${data.correct_answer}`;
        } else if (data.has_answer) {
            fb.textContent = `✗ 錯誤！正確答案是 ${data.correct_option}`;
        } else {
            fb.textContent = "✗ 錯誤！此題暫無官方答案";
        }
        fb.className = "feedback err";
        $("quiz-next").disabled = false;
    }
}

async function quizAdvance() {
    clearTimeout(quizAutoTimer);
    const data = await apiPost("/api/quiz/next", {});
    if (data.finished) { await quizEnd(); return; }
    renderQuizQuestion(data);
}

async function quizEnd() {
    const res = await apiPost("/api/quiz/end", {});
    const r = res.record || {};
    alert(
        `測驗完成！\n\n總題數：${r.total_questions}\n正確：${r.correct_answers}\n` +
        `準確率：${(r.accuracy || 0).toFixed(1)}%\n耗時：${Math.round(r.spent_time || 0)}秒`
    );
    quizStarted = false;
    setQuizSettings(true);
    $("quiz-question").textContent = "";
    $("quiz-options").innerHTML = "";
    $("quiz-feedback").textContent = "";
    $("quiz-next").disabled = true;
    $("quiz-score").textContent = "目前成績：0/0";
    $("quiz-stats").textContent = "";
    $("quiz-bar").style.width = "0%";
}

async function quizReset() {
    if (quizStarted && !confirm("確定要丟棄目前進度並清空測驗，重新設定參數嗎？")) return;
    clearTimeout(quizAutoTimer);
    await apiPost("/api/quiz/reset", {});
    quizStarted = false;
    setQuizSettings(true);
    $("quiz-question").textContent = "";
    $("quiz-options").innerHTML = "";
    $("quiz-feedback").textContent = "";
    $("quiz-next").disabled = true;
    $("quiz-score").textContent = "目前成績：0/0";
    $("quiz-stats").textContent = "";
    $("quiz-bar").style.width = "0%";
}

$("quiz-start").addEventListener("click", quizStart);
$("quiz-next").addEventListener("click", quizAdvance);
$("quiz-reset").addEventListener("click", quizReset);

// ==================== 模組4：新增單字 / 自訂詞庫 ====================
let selectedCustomRow = -1;

function setAddMessage(text, isError) {
    const el = $("add-message");
    el.textContent = text;
    el.style.color = isError ? "var(--error-text)" : "var(--success-text)";
}

async function lookupWord() {
    const word = $("lookup-word").value.trim();
    if (!word) { setAddMessage("請先輸入英文單字", true); return; }

    $("lookup-btn").disabled = true;
    $("add-btn").disabled = true;
    setAddMessage("查詢中，請稍候...", false);

    const data = await apiPost("/api/lookup", { word });
    $("lookup-btn").disabled = false;

    if (!data.success) {
        $("add-english").value = "";
        $("add-chinese").value = "";
        $("add-pos").value = "";
        setAddMessage(data.error || "查詢失敗", true);
        return;
    }
    $("add-english").value = data.english || "";
    $("add-chinese").value = data.chinese || "";
    $("add-pos").value = data.part_of_speech || "";
    $("add-btn").disabled = false;
    setAddMessage(data.warning ? `查詢完成：${data.warning}` : "查詢完成，可直接加入自訂詞庫", false);
}

async function addCustom() {
    const data = await apiPost("/api/custom/add", {
        english: $("add-english").value.trim(),
        chinese: $("add-chinese").value.trim(),
        pos: $("add-pos").value.trim(),
    });
    if (!data.ok) { setAddMessage(data.message, true); return; }
    setAddMessage(data.message, false);
    $("add-btn").disabled = true;
    loadCustomTable();
}

async function loadCustomTable() {
    const data = await apiGet("/api/custom");
    const tbody = $("custom-table").querySelector("tbody");
    tbody.innerHTML = "";
    selectedCustomRow = -1;

    (data.words || []).forEach((w, index) => {
        const tr = document.createElement("tr");
        ["english", "chinese", "part_of_speech"].forEach((key) => {
            const td = document.createElement("td");
            td.contentEditable = "true";
            td.textContent = w[key] || "";
            tr.appendChild(td);
        });
        tr.addEventListener("click", () => {
            tbody.querySelectorAll("tr").forEach((r) => r.classList.remove("selected"));
            tr.classList.add("selected");
            selectedCustomRow = index;
        });
        tbody.appendChild(tr);
    });
}

async function saveCustom() {
    const rows = [];
    $("custom-table").querySelectorAll("tbody tr").forEach((tr) => {
        const cells = tr.querySelectorAll("td");
        rows.push({
            english: cells[0].textContent.trim(),
            chinese: cells[1].textContent.trim(),
            part_of_speech: cells[2].textContent.trim(),
        });
    });
    const data = await apiPost("/api/custom/save", { rows });
    if (!data.ok) { setAddMessage(data.message, true); return; }
    setAddMessage(data.message, false);
    alert("自訂詞庫已更新");
    loadCustomTable();
}

async function deleteCustom() {
    if (selectedCustomRow < 0) { setAddMessage("請先選取要刪除的單字", true); return; }
    if (!confirm("確定要刪除選取的自訂單字？")) return;
    await apiPost("/api/custom/delete", { index: selectedCustomRow });
    setAddMessage("已刪除選取單字", false);
    loadCustomTable();
}

$("lookup-btn").addEventListener("click", lookupWord);
$("lookup-word").addEventListener("keydown", (e) => { if (e.key === "Enter") lookupWord(); });
$("add-btn").addEventListener("click", addCustom);
$("custom-refresh").addEventListener("click", loadCustomTable);
$("custom-save").addEventListener("click", saveCustom);
$("custom-delete").addEventListener("click", deleteCustom);

// ==================== 模組5：測驗紀錄 ====================
async function loadRecords() {
    const type = encodeURIComponent($("records-type").value);
    const data = await apiGet(`/api/records?type=${type}`);
    const tbody = $("records-table").querySelector("tbody");
    tbody.innerHTML = "";

    (data.records || []).forEach((r) => {
        const tr = document.createElement("tr");
        [
            r.completed_at,
            r.item_name,
            r.record_type,
            String(r.total_questions),
            String(r.correct_answers),
            `${(r.accuracy || 0).toFixed(1)}%`,
        ].forEach((v) => {
            const td = document.createElement("td");
            td.textContent = v;
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
    $("records-summary").textContent = `共 ${data.count} 筆紀錄`;
}

$("records-type").addEventListener("change", loadRecords);
$("records-refresh").addEventListener("click", loadRecords);

// ==================== 初始化 ====================
refreshVocabStats();
