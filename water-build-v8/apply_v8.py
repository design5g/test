from pathlib import Path
import re, sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'ishrab_v3')

def rw(path, fn):
 p=root/path; p.write_text(fn(p.read_text()))

rw(Path('app/build.gradle'),lambda s:s.replace("applicationId 'com.ishrab.smarthealth.ai.v7'","applicationId 'com.ishrab.smarthealth.ai.v8'").replace('versionCode 7','versionCode 8').replace("versionName '7.0'","versionName '8.0'"))

def model(s):
 s=s.replace('official Qwen3-0.6B Q8_0','official LiquidAI LFM2.5-350M Q4_0').replace('Qwen3-0.6B-Q8_0.gguf','LFM2.5-350M-Q4_0.gguf').replace('639_446_688L','219_309_792L').replace('9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031','85e32858daafad55b7bcd6b97a1343ee0661188e8036f9862d14d6b563142f50')
 s=re.sub(r'private static final String\[] URLS = \{.*?\n    \};','''private static final String[] URLS = {
            "https://huggingface.co/LiquidAI/LFM2.5-350M-GGUF/resolve/main/LFM2.5-350M-Q4_0.gguf?download=true",
            "https://huggingface.co/LiquidAI/LFM2.5-350M-GGUF/resolve/main/LFM2.5-350M-Q4_0.gguf"
    };''',s,flags=re.S)
 for a,b in [('qwen_v7_verified','lfm_v8_verified'),('qwen_v7_sha256','lfm_v8_sha256'),('qwen_v7_bytes','lfm_v8_bytes'),('qwen_v7_installed_at','lfm_v8_installed_at')]:s=s.replace(a,b)
 return s.replace('تنزيل حزمة Qwen الرسمية؛ يمكن استئنافها إذا انقطع الاتصال…','تنزيل حزمة LFM2.5 الرسمية السريعة؛ يمكن استئنافها إذا انقطع الاتصال…').replace('Downloading the official Qwen pack; interrupted downloads can resume…','Downloading the official fast LFM2.5 pack; interrupted downloads can resume…').replace('+ 160L * 1024L * 1024L','+ 80L * 1024L * 1024L').replace('Ishrab-Smart-Health-V7/7.0 Android','Ishrab-Smart-Health-V8/8.0 Android')
rw(Path('app/src/main/java/com/ishrab/smarthealth/ModelManager.java'),model)

def graph(s):
 old='''    public String promptSummary() {
        List<Association> items = refresh();
        if (items.isEmpty()) return "No stable personal associations yet; personal data are still sparse.";
        StringBuilder b = new StringBuilder();
        int n = 0;
        for (Association a : items) {
            if (n++ >= 6) break;
            b.append("- PERSONAL ASSOCIATION (not causation): ").append(a.enTitle).append(". ")
                    .append(a.enDetail).append(" [strength=").append(String.format(Locale.US, "%.2f", a.strength))
                    .append(", support=").append(a.support).append("]\\n");
        }
        return b.toString();
    }
'''
 new='''    public String promptSummary() { return promptSummary(4); }

    public String promptSummary(int max) {
        List<Association> items = current();
        if (items.isEmpty()) return "No stable personal associations yet; personal data are still sparse.";
        StringBuilder b = new StringBuilder();
        int n = 0;
        for (Association a : items) {
            if (n++ >= Math.max(1, max)) break;
            b.append("- PERSONAL ASSOCIATION (not causation): ").append(a.enTitle).append(". ")
                    .append(a.enDetail).append(" [strength=").append(String.format(Locale.US, "%.2f", a.strength))
                    .append(", support=").append(a.support).append("]\\n");
        }
        return b.toString();
    }
'''
 assert old in s;return s.replace(old,new)
rw(Path('app/src/main/java/com/ishrab/smarthealth/HealthGraphEngine.java'),graph)

def llm(s):
 s=s.replace('/** Actual local Qwen + llama.cpp reasoning orchestrator with local medical RAG and a fixed safety core. */','/** Fast hybrid local AI: instant structured analytics plus LFM2.5 synthesis, medical RAG, memory, and a fixed safety core. */')
 s=s.replace('''        return ar
                ? "Qwen3‑0.6B Q8_0 فعلي عبر llama.cpp + استرجاع 100,000 وحدة دليل طبي + ذاكرة صحية شخصية"
                : "Real Qwen3‑0.6B Q8_0 via llama.cpp + retrieval over 100,000 medical evidence units + personal health memory";''','''        return ar
                ? "LFM2.5‑350M Q4_0 سريع عبر llama.cpp + مسار فوري للأسئلة الشائعة + 100,000 وحدة دليل طبي"
                : "Fast LFM2.5‑350M Q4_0 via llama.cpp + instant lane for common questions + 100,000 medical evidence units";''')
 a=s.index('    public void chat(String question, HealthStore store, LocalAiEngine analytics, Callback callback) {');b=s.index('    private ModelManager.Callback bridge(Callback callback) {',a)
 chat='''    public void chat(String question, HealthStore store, LocalAiEngine analytics, Callback callback) {
        boolean ar = containsArabic(question) || store.ar();
        LearningMemory quickMemory = new LearningMemory(store);
        LearningMemory.CommandResult command = quickMemory.handleCommand(question, ar);
        if (command.handled) { callback.onComplete(new AiResult(command.response, new ArrayList<>(), 100, "memory_command", 0, new SmartEngine(store).trackingCompleteness())); return; }
        String blocked = SafetyCore.preflight(question, ar);
        if (blocked != null) { callback.onComplete(new AiResult(blocked, new ArrayList<>(), 100, "safety_core", 0, new SmartEngine(store).trackingCompleteness())); return; }
        LocalAiEngine.IntentResult intent = analytics.classify(question);
        int coverage = new SmartEngine(store).trackingCompleteness();
        if (shouldUseFastLane(question, intent)) {
            callback.onStatus(ar ? "فهم سريع…" : "Fast understanding…");
            String answer = SafetyCore.sanitizeGenerated(analytics.reply(question), ar);
            callback.onComplete(new AiResult(answer, new ArrayList<>(), Math.min(94, 58 + coverage / 2), "fast_local_" + intent.intent, store.array("ai_hypotheses").length(), coverage));
            return;
        }
        if (!busy.compareAndSet(false, true)) { callback.onError(new IllegalStateException(ar ? "الذكاء يجيب عن سؤال آخر الآن" : "The AI is answering another question")); return; }
        worker.execute(() -> {
            try {
                callback.onStatus(ar ? "فهم سريع…" : "Fast understanding…");
                File model = modelManager.ensureInstalled(ar, bridge(callback)); load(model, ar, callback);
                LearningMemory memory = new LearningMemory(store); HealthGraphEngine graph = new HealthGraphEngine(store);
                SelfModelEngine self = new SelfModelEngine(store, memory, graph, modelManager, knowledge);
                String retrievalQuery = FastMedicalQuery.build(question, intent.intent);
                callback.onStatus(ar ? "بحث في الأدلة…" : "Searching evidence…");
                List<MedicalKnowledge.Hit> hits = knowledge.search(retrievalQuery, 5);
                callback.onStatus(ar ? "صياغة الجواب…" : "Writing the answer…");
                String raw = engine.generate(buildGroundedPrompt(question, store, analytics, memory, graph, self, hits, ar), 256); generatedTurns++;
                String answer = SafetyCore.sanitizeGenerated(cleanAnswer(raw), ar);
                if (answer.isEmpty()) throw new IllegalStateException(ar ? "لم ينتج النموذج إجابة" : "The model produced no answer");
                int grounding = groundingScore(hits, graph.associationCount(), coverage); memory.observe(question, intent.intent, intent.confidence, answer);
                callback.onComplete(new AiResult(answer, hits, grounding, retrievalQuery, graph.associationCount(), coverage)); if (generatedTurns >= 12) resetContext();
            } catch (Throwable error) { callback.onError(error); } finally { busy.set(false); }
        });
    }

    private boolean shouldUseFastLane(String question, LocalAiEngine.IntentResult intent) {
        if (intent == null || intent.confidence < 0.84) return false;
        String q = question == null ? "" : question.toLowerCase(Locale.ROOT);
        String[] deep = {"لماذا", "السبب", "سبب", "اربط", "العلاقة", "حلل بعمق", "فسر", "why", "cause", "connect", "relationship", "evidence", "deep analysis"};
        for (String x : deep) if (q.contains(x)) return false;
        switch (intent.intent) {
            case "greeting": case "gratitude": case "help": case "preferences": case "language": case "memory_recall": case "summary": case "glucose": case "hydration": case "activity": case "weight": case "a1c": case "comparison": case "motivation": case "explanation": return true;
            default: return false;
        }
    }

'''
 s=s[:a]+chat+s[b:]
 s=s.replace('callback.onStatus(ar ? "تحميل أوزان Qwen إلى الذاكرة…" : "Loading Qwen weights into memory…");','callback.onStatus(ar ? "تحميل LFM2.5 السريع إلى الذاكرة…" : "Loading fast LFM2.5 into memory…");')
 s=re.sub(r'\n    private String makeRetrievalQuery\(String question\) \{.*?\n    \}\n\n    private String buildGroundedPrompt','\n\n    private String buildGroundedPrompt',s,flags=re.S)
 s=s.replace('StringBuilder p = new StringBuilder(16_000);','StringBuilder p = new StringBuilder(9_000);').replace('memory.relevantMemories(question, 5)','memory.relevantMemories(question, 3)').replace('graph.promptSummary()','graph.promptSummary(4)')
 x=s.index('        p.append("ANSWER_RULES\\n")');y=s.index('        return p.toString();',x)
 rules='''        p.append("ANSWER_RULES\\n")
                .append("DIRECT RESPONSE MODE. Answer immediately. Never narrate analysis, planning, hidden reasoning, or chain-of-thought.\\n")
                .append("Use 4-8 short sentences or at most 6 concise bullets. Do not restate the question and do not add a long preamble.\\n")
                .append("Connect tracked timeline, relevant memory, personal associations, and retrieved evidence. Separate GENERAL EVIDENCE from PERSONAL ASSOCIATIONS; association is not causation.\\n")
                .append("Cite only supporting evidence as [E1], [E2], etc. State missing data and uncertainty briefly. Give at most three low-risk next steps.\\n")
                .append("Never calculate insulin or medication doses, stop/change treatment, diagnose, call estimated A1C a lab result, or override clinician-set fluid limits. Emergency signs require urgent evaluation.\\n")
                .append("You are software, not conscious. Answer in the user's language with a calm, direct tone.");
'''
 s=s[:x]+rules+s[y:]
 s=re.sub(r'    private String systemPrompt\(\) \{.*?\n    \}','''    private String systemPrompt() {
        return "You are Ishrab Fast Health AI V8, a bilingual Arabic-English on-device health assistant using LFM2.5-350M. " +
                "DIRECT RESPONSE MODE: answer immediately and concisely. Never generate, narrate, or reveal chain-of-thought, hidden reasoning, planning, or scratch work. " +
                "Prefer 4-8 short sentences or at most 6 bullets. Do not repeat the user's question. " +
                "Use retrieved medical evidence only for claims it supports. Combine it with time-stamped personal data, persistent memory, and personal associations while distinguishing association from causation. " +
                "The medical safety core is immutable: never diagnose, prescribe, calculate insulin or medication doses, change or stop treatment, override a clinician-set fluid limit, or present estimated A1C as a laboratory result. " +
                "For loss of consciousness, confusion, breathing difficulty, chest pain, repeated vomiting, fruity breath, or ketones with high glucose, advise urgent emergency evaluation. " +
                "Match the user's language. You are software and must not claim literal consciousness or feelings.";
    }''',s,count=1,flags=re.S)
 return s
rw(Path('app/src/main/java/com/ishrab/smarthealth/RealLlmEngine.java'),llm)

def mainui(s):
 pairs=[
 ('new String[]{"اليوم","السكر","الاتجاهات","العقل","الإعدادات"}:new String[]{"Today","Glucose","Trends","Mind","Settings"}','new String[]{"اليوم","السجل","الرؤى","AI","الإعدادات"}:new String[]{"Today","Log","Insights","AI","Settings"}'),
 ('(ar?"AI جاهز":"AI ready"):(ar?"إعداد AI":"AI setup")','(ar?"AI سريع":"Fast AI"):(ar?"إعداد AI":"AI setup")'),
 ('c.setBackground(round(surface,22,1));c.setElevation(dp(2));c.setLayoutParams(marginTop(10));','c.setBackground(round(surface,24,1));c.setElevation(dp(1));c.setLayoutParams(marginTop(8));'),
 ('v.setPadding(dp(14),dp(12),dp(14),dp(12));v.setBackground(round(color,16,0));','v.setMinHeight(dp(48));v.setPadding(dp(14),dp(12),dp(14),dp(12));v.setBackground(round(color,18,0));'),
 ('v.setPadding(dp(12),dp(10),dp(12),dp(10));v.setBackground(roundTransparent(color,15));','v.setMinHeight(dp(48));v.setPadding(dp(12),dp(10),dp(12),dp(10));v.setBackground(roundTransparent(color,18));'),
 ('ar?"تسجيل سريع مترابط":"Connected quick logging"','ar?"إضافة سريعة":"Quick add"'),('ar?"كل سجل يحدّث التحليلات والتنبيهات والتقرير تلقائيًا":"Every entry updates insights, reminders, and reports automatically"','ar?"لمسة واحدة أو نموذج مختصر؛ كل إضافة تحدث التحليل تلقائيًا":"One tap or a short form; every entry updates analysis automatically"'),
 ('quick.addView(q2,marginTop(8));c.addView(quick);','quick.addView(q2,marginTop(8));quick.addView(button(ar?"اسأل AI الآن":"Ask AI now",accent,v->showAiChat()),marginTop(8));c.addView(quick);'),
 ('ar?"العقل الصحي المتكيف V7":"Adaptive health mind V7"','ar?"المساعد الصحي السريع V8":"Fast health AI V8"'),('ar?"استدلال فعلي + ذاكرة + رسم صحي":"Real reasoning + memory + health graph"','ar?"رد مباشر + ذاكرة + رسم صحي":"Direct response + memory + health graph"'),('aiStat(ar?"المعرفة":"Knowledge","100K")','aiStat(ar?"الوضع":"Mode",ar?"سريع":"Fast")'),('ar?"دردشة العقل":"Chat with AI"','ar?"اسأل AI":"Ask AI"'),
 ('ar?"العقل الصحي V7":"Health reasoning AI V7"','ar?"المساعد الصحي السريع V8":"Fast Health AI V8"'),('top.addView(chip(ar?"محلي بعد الإعداد":"Local after setup",realAi.isModelInstalled()?success:warning));','top.addView(chip(ar?"رد مباشر":"Direct",realAi.isModelInstalled()?success:warning));'),('ar?"Qwen + llama.cpp · 100,000 وحدة دليل طبي · الذاكرة والرسم الصحي":"Qwen + llama.cpp · 100,000 medical evidence units · memory and health graph"','ar?"LFM2.5 350M · وضع مباشر · 100K دليل طبي":"LFM2.5 350M · Direct mode · 100K medical evidence"'),
 ('ar?"مرحبًا. أنا برنامج استدلال صحي محلي بذاكرة شخصية. أربط سجلك بالأدلة المسترجعة وأوضح ما أعرفه وما ينقصني. لست وعيًا بشريًا، ولن أغير جرعة أو علاجًا.":"Hello. I am local health reasoning software with personal memory. I connect your log with retrieved evidence and state what I know and what is missing. I am not human consciousness and I will not change doses or treatment."','ar?"أجيب مباشرة. الأسئلة الشائعة تُحل فورًا، والأسئلة المركبة تستخدم LFM2.5 مع الأدلة والذاكرة. لا أعرض تفكيرًا داخليًا طويلًا، ولا أغيّر جرعة أو علاجًا.":"I answer directly. Common questions are handled instantly; complex questions use LFM2.5 with evidence and memory. I do not show long internal reasoning or change doses or treatment."'),
 ('new String[]{"حلل كل ما حدث اليوم","ما أقوى علاقة اكتشفتها؟","توقع اتجاه A1C واشرح السبب","ماذا ينقصك لتفهمني أفضل؟"}:new String[]{"Analyze everything that happened today","What is your strongest discovered association?","Forecast my A1C trend and explain why","What data do you need to understand me better?"}','new String[]{"لخص يومي","حلل السكر","اربط الرياضة بالسكر","توقع A1C"}:new String[]{"Summarize today","Analyze glucose","Link activity and glucose","Forecast A1C"}'),('ar?"اسأل عن بياناتك أو علاقة صحية":"Ask about your data or a health relationship"','ar?"اكتب سؤالك باختصار…":"Type a short question…"'),('ar?"أجمع بياناتك وذاكرتي والأدلة…":"Gathering your data, memory, and evidence…"','ar?"فهم السؤال…":"Understanding…"'),('for(int i=0;i<Math.min(4,result.evidence.size());i++)','for(int i=0;i<Math.min(2,result.evidence.size());i++)'),
 ('ar?"الحقول فارغة عمدًا. أدخل بياناتك الفعلية؛ تبقى محفوظة محليًا. حزمة Qwen تُنزّل مرة واحدة باختيارك ثم يعمل الاستدلال محليًا.":"Fields are intentionally empty. Enter your actual data; it stays on-device. The Qwen pack is downloaded once when you choose, then reasoning runs locally."','ar?"الحقول فارغة عمدًا. أدخل بياناتك الفعلية؛ تبقى محليًا. حزمة LFM2.5 الخفيفة تُنزّل مرة واحدة باختيارك، وبعدها يعمل المساعد محليًا بوضع الرد المباشر.":"Fields are intentionally empty. Enter your actual data; it stays on-device. The lightweight LFM2.5 pack downloads once when you choose, then the assistant runs locally in direct-response mode."'),
 ('ar?"إعداد العقل المحلي V7":"Set up local AI V7"','ar?"إعداد المساعد السريع V8":"Set up fast AI V8"'),('ar?"التطبيق جاهز للتسجيل والتحليل الحسابي. لتفعيل الدردشة الاستدلالية الفعلية سيُنزل نموذج Qwen3‑0.6B Q8_0 بحجم يقارب 639 MB لمرة واحدة، ثم يعمل محليًا. يمكنك تأجيل ذلك.":"Tracking and deterministic analytics are ready. To enable actual reasoning chat, the app downloads Qwen3‑0.6B Q8_0 (~639 MB) once, then runs locally. You can postpone this."','ar?"التسجيل والتحليل السريع جاهزان الآن. لتفعيل الدردشة المركبة سيُنزل نموذج LFM2.5‑350M Q4_0 بحجم يقارب 209 MiB لمرة واحدة. صُممت النسخة للرد المباشر دون تفكير طويل، ثم تعمل محليًا. يمكنك تأجيل ذلك.":"Fast tracking and analytics are ready now. Complex chat downloads LFM2.5‑350M Q4_0 (~209 MiB) once. This version is tuned for direct responses without long thinking, then runs locally. You can postpone setup."')]
 for a,b in pairs:s=s.replace(a,b)
 s=s.replace('Qwen','LFM2.5').replace('V7','V8').replace('#F5F8FC','#F3F7FA').replace('#EAF1F6','#E9F3F4').replace('#102A43','#0B2333').replace('#657786','#6B7F8C').replace('إعداد نموذج LFM2.5 الآن (~639 MB)','إعداد LFM2.5 الآن (~209 MiB)').replace('Set up LFM2.5 now (~639 MB)','Set up LFM2.5 now (~209 MiB)')
 return s
rw(Path('app/src/main/java/com/ishrab/smarthealth/MainActivity.java'),mainui)
rw(Path('app/src/main/java/com/ishrab/smarthealth/SelfModelEngine.java'),lambda s:s.replace('حزمة Qwen','حزمة LFM2.5').replace('Qwen pack','LFM2.5 pack').replace('qwen_ready=','lfm2_5_ready='))
print('V8 transformations applied')
