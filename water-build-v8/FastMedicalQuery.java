package com.ishrab.smarthealth;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

/** Deterministic bilingual medical query builder. It avoids a second LLM generation before RAG. */
public final class FastMedicalQuery {
    private FastMedicalQuery() {}

    public static String build(String question, String intent) {
        String n = normalize(question);
        LinkedHashSet<String> out = new LinkedHashSet<>();
        addMapped(n, out);
        addIntent(intent, out);
        for (String token : n.split("\\s+")) {
            if (token.length() >= 3 && !STOP.contains(token) && isLatin(token)) out.add(token);
            if (out.size() >= 14) break;
        }
        if (out.isEmpty()) addIntent(intent, out);
        StringBuilder b = new StringBuilder();
        for (String x : out) { if (x.isEmpty()) continue; if (b.length() > 0) b.append(' '); b.append(x); if (b.length() >= 180) break; }
        return b.toString().trim();
    }

    private static void addMapped(String q, Set<String> out) {
        map(q,out,"سكر","diabetes","glucose"); map(q,out,"جلوكوز","glucose"); map(q,out,"تراكمي","a1c","glycated hemoglobin");
        map(q,out,"صائم","fasting glucose"); map(q,out,"قبل الوجبه","premeal glucose"); map(q,out,"بعد الوجبه","postprandial glucose");
        map(q,out,"ماء","hydration","fluid intake"); map(q,out,"ترطيب","hydration"); map(q,out,"عطش","thirst"); map(q,out,"تبول","urination");
        map(q,out,"وزن","body weight"); map(q,out,"مشي","walking","exercise"); map(q,out,"رياضه","physical activity","exercise"); map(q,out,"نشاط","physical activity");
        map(q,out,"كربوهيدرات","carbohydrate","glucose"); map(q,out,"صيام","fasting","diabetes"); map(q,out,"كيتون","ketones","diabetic ketoacidosis");
        map(q,out,"قيء","vomiting"); map(q,out,"تنفس","breathing difficulty"); map(q,out,"دوخه","dizziness"); map(q,out,"توتر","stress","glucose");
        map(q,out,"نوم","sleep","glucose"); map(q,out,"قلب","heart disease","fluid"); map(q,out,"كلي","kidney disease","fluid"); map(q,out,"حمل","pregnancy","diabetes");
        map(q,out,"تورم","swelling","edema"); map(q,out,"انسولين","insulin","diabetes");
    }

    private static void addIntent(String intent, Set<String> out) {
        if (intent == null) return;
        switch (intent) {
            case "a1c": out.add("a1c"); out.add("average glucose"); break;
            case "glucose": out.add("glucose"); out.add("diabetes"); break;
            case "hydration": out.add("hydration"); out.add("fluid intake"); break;
            case "activity": out.add("exercise"); out.add("physical activity"); out.add("glucose"); break;
            case "weight": out.add("body weight"); out.add("weight change"); break;
            case "patterns": case "comparison": out.add("glucose pattern"); out.add("self monitoring"); break;
            case "recommendations": out.add("diabetes self management"); out.add("lifestyle"); break;
            case "safety": out.add("diabetes emergency symptoms"); break;
            default: out.add("health self monitoring");
        }
    }

    private static void map(String q, Set<String> out, String needle, String... terms) { if (q.contains(normalize(needle))) for (String t : terms) out.add(t); }
    private static boolean isLatin(String s) { return s.matches(".*[a-z].*"); }
    private static String normalize(String s) {
        String x=(s==null?"":s).toLowerCase(Locale.ROOT).replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي');
        return x.replaceAll("[\\u064B-\\u065F\\u0670]","").replaceAll("[^\\p{L}\\p{N}]+"," ").trim();
    }
    private static final Set<String> STOP = new java.util.HashSet<String>() {{
        add("what"); add("why"); add("how"); add("when"); add("with"); add("from"); add("this"); add("that"); add("about"); add("please"); add("could"); add("would"); add("have"); add("does"); add("into");
    }};
}
