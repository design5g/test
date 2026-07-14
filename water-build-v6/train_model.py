import json, random, re, sys
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

random.seed(20260714)

INTENTS = {
'a1c': {
'ar':['توقع السكر التراكمي بعد شهر','كم سيكون التراكمي','حلل اتجاه الهيموغلوبين السكري','ما تقدير A1C','هل التراكمي يتحسن','اعرض توقع التراكمي','احسب اتجاه السكر التراكمي'],
'en':['forecast my a1c next month','what will my a1c be','analyze the a1c trend','estimate glycated hemoglobin','is my a1c improving','show my a1c forecast','calculate the a1c trajectory']},
'activity': {
'ar':['حلل نشاطي اليومي','ما تأثير الرياضة على السكر','كم مشيت اليوم','اربط المشي بالقراءات','حلل مدة التمرين','هل الجري حسن السكر','ما نتيجة النشاط'],
'en':['analyze my daily activity','how does exercise affect glucose','how much did i walk today','link walking with readings','analyze workout duration','did running improve glucose','what is the activity result']},
'glucose': {
'ar':['حلل قراءات السكر','ما متوسط السكر اليوم','لماذا ارتفع السكر','هل القراءة طبيعية بالنسبة لهدفي','اعرض اتجاه الجلوكوز','ما آخر قراءة سكر','قارن قراءات الصيام وبعد الطعام'],
'en':['analyze my glucose readings','what is today glucose average','why did glucose rise','is the reading within my target','show the glucose trend','what is my latest glucose reading','compare fasting and post meal readings']},
'greeting': {
'ar':['مرحبا','السلام عليكم','اهلا يا مساعد','صباح الخير','مساء الخير','كيف حالك','ابدأ المحادثة'],
'en':['hello','hi assistant','good morning','good evening','how are you','start the chat','hey health assistant']},
'help': {
'ar':['ماذا تستطيع أن تفعل','ساعدني','كيف استخدم المساعد','اعرض الأوامر','ما الأسئلة التي تفهمها','اشرح قدراتك','احتاج مساعدة'],
'en':['what can you do','help me','how do i use the assistant','show commands','what questions do you understand','explain your capabilities','i need help']},
'hydration': {
'ar':['هل شربت ماء كفاية','حلل الترطيب','كم تبقى من هدف الماء','اربط الماء بالسكر','ما كمية الماء اليوم','هل احتاج كوب ماء','اعرض تقدم الشرب'],
'en':['did i drink enough water','analyze hydration','how much remains of my water goal','link water with glucose','how much water today','do i need a glass of water','show drinking progress']},
'patterns': {
'ar':['ما الأنماط التي اكتشفتها','ابحث عن علاقة بين البيانات','ما الذي يتكرر في سجلي','حلل الارتباطات','اكتشف نمط السكر','ما ملاحظاتك على الأسبوع','هل توجد علاقة واضحة'],
'en':['what patterns did you find','look for relationships in my data','what repeats in my log','analyze correlations','detect a glucose pattern','what did you notice this week','is there a clear relationship']},
'recommendations': {
'ar':['ماذا تنصحني اليوم','اعطني خطوات عملية','ما الذي يمكنني تحسينه','اقترح عادة صحية','ما أولويتي اليوم','اعطني توصية آمنة','كيف أحسن الالتزام'],
'en':['what do you recommend today','give me practical steps','what can i improve','suggest a healthy habit','what is my priority today','give a safe recommendation','how can i improve adherence']},
'safety': {
'ar':['هل هذه الأعراض خطرة','متى أتصل بالطوارئ','عندي قيء وكيتونات','السكر منخفض جدا','أشعر بدوخة شديدة','عندي صعوبة تنفس','ما علامات الخطر'],
'en':['are these symptoms dangerous','when should i call emergency services','i have vomiting and ketones','glucose is very low','i feel severe dizziness','i have difficulty breathing','what are the warning signs']},
'summary': {
'ar':['لخص يومي','اعطني ملخص اليوم','ماذا حدث اليوم','اعرض تقريرا سريعا','لخص الماء والسكر والنشاط','ملخص صحي','كيف كان يومي'],
'en':['summarize my day','give me today summary','what happened today','show a quick report','summarize water glucose and activity','health summary','how was my day']},
'weight': {
'ar':['حلل وزني','ما اتجاه الوزن','هل وزني ينخفض','قارن الوزن هذا الشهر','كم تغير وزني','اعرض بوصلة الوزن','اربط الوزن بالنشاط'],
'en':['analyze my weight','what is the weight trend','is my weight decreasing','compare weight this month','how much did my weight change','show the weight compass','link weight with activity']},
'memory_store': {
'ar':['تذكر أنني أحب المشي','احفظ هذه المعلومة','تعلم أنني أعمل ليلا','لا تنس أن هدفي كذا','سجل تفضيلي','من الآن تذكر هذا','أريدك أن تحفظ معلومة'],
'en':['remember that i like walking','save this information','learn that i work nights','do not forget my goal','record my preference','remember this from now on','i want you to store a fact']},
'memory_recall': {
'ar':['ماذا تتذكر عني','اعرض ذاكرتك','ما المعلومات التي حفظتها','هل تتذكر تفضيلي','اذكر ما تعلمته مني','ما الذي تعرفه عني','استرجع الذكريات'],
'en':['what do you remember about me','show your memory','what information did you save','do you remember my preference','tell me what you learned from me','what do you know about me','recall memories']},
'correction': {
'ar':['صحح إجابتك','الجواب السابق غير صحيح','تعلم التصحيح التالي','عندما أسألك هكذا أجب هكذا','هذه المعلومة تحتاج تصحيح','لا تكرر هذا الخطأ','سأعلمك الإجابة الصحيحة'],
'en':['correct your answer','the previous answer is wrong','learn this correction','when i ask this answer that','this information needs correction','do not repeat this mistake','i will teach you the correct answer']},
'preferences': {
'ar':['أجب باختصار','أريد شرحا مفصلا','نادني باسمي','استخدم العربية دائما','تكلم بطريقة أبسط','اجعل أسلوبك رسمي','ما تفضيلات التواصل'],
'en':['answer briefly','i want a detailed explanation','call me by my name','always use english','speak more simply','use a formal style','what are my communication preferences']},
'motivation': {
'ar':['شجعني','احتاج تحفيزا','ساعدني على الالتزام','ذكرني لماذا أستمر','اعطني رسالة إيجابية','احتفل بتقدمي','كيف أحافظ على العادة'],
'en':['encourage me','i need motivation','help me stay consistent','remind me why to continue','give me a positive message','celebrate my progress','how do i keep the habit']},
'explanation': {
'ar':['اشرح كيف وصلت للنتيجة','ما البيانات التي استخدمتها','لماذا قلت ذلك','اشرح التحليل ببساطة','ما درجة الثقة','كيف يعمل النموذج','اعرض أسباب الاستنتاج'],
'en':['explain how you reached the result','what data did you use','why did you say that','explain the analysis simply','what is the confidence','how does the model work','show the reasons for the conclusion']},
'comparison': {
'ar':['قارن اليوم بالأمس','قارن هذا الأسبوع بالسابق','ما الفرق بين الصيام وبعد الوجبة','قارن الماء والنشاط','هل تحسنت عن الشهر الماضي','اعرض مقارنة زمنية','قارن فترتين'],
'en':['compare today with yesterday','compare this week with the previous one','difference between fasting and post meal','compare hydration and activity','did i improve from last month','show a time comparison','compare two periods']},
'gratitude': {
'ar':['شكرا','ممتاز','أحسنت','هذا مفيد','بارك الله فيك','رائع يا مساعد','شكرا على التحليل'],
'en':['thank you','great','well done','that is helpful','excellent assistant','nice analysis','thanks for the explanation']},
'language': {
'ar':['تحدث بالعربية','ترجم للإنجليزية','اكتب بلغة عربية واضحة','غير اللغة','استخدم المصطلحات الإنجليزية','أجب باللغتين','صحح لغتي'],
'en':['speak in english','translate to arabic','use clear english','change the language','use arabic terms','answer bilingually','correct my language']},
}

MOD_AR = ['اليوم','هذا الأسبوع','بشكل واضح','من فضلك','اعتمادا على سجلي','بصورة مختصرة','بالتفصيل','الآن','مع ذكر الثقة','دون مبالغة']
MOD_EN = ['today','this week','clearly','please','using my log','briefly','in detail','now','with confidence','without exaggeration']
PREFIX_AR = ['','يا مساعد ','أريدك أن ','هل يمكنك أن ','من فضلك ','أحتاج أن ']
PREFIX_EN = ['','assistant ','please ','can you ','i want you to ','i need you to ']
SUFFIX_AR = ['','؟','.',' لو سمحت',' مع توضيح السبب',' وبطريقة سهلة']
SUFFIX_EN = ['','?','.',' please',' with the reason',' in simple language']

SLOTS_AR = ['السكر','الجلوكوز','الماء','الترطيب','الوزن','المشي','الجري','النشاط','الوجبة','الصيام','التراكمي','العادات','الأعراض','التوتر']
SLOTS_EN = ['glucose','blood sugar','water','hydration','weight','walking','running','activity','meal','fasting','a1c','habits','symptoms','stress']

def normalize(s):
    s=s.lower().replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي')
    s=re.sub(r'[\u064B-\u065F\u0670]','',s)
    s=re.sub(r'[^\w\u0600-\u06ff]+',' ',s,flags=re.UNICODE).strip()
    return s

texts=[]; labels=[]
for intent, langs in INTENTS.items():
    for lang in ('ar','en'):
        target=250
        bases=langs[lang]
        seen=set()
        tries=0
        while len(seen)<target and tries<20000:
            tries+=1
            if lang=='ar':
                s=random.choice(PREFIX_AR)+random.choice(bases)
                if random.random()<0.72: s+=' '+random.choice(MOD_AR)
                if random.random()<0.25: s+=' عن '+random.choice(SLOTS_AR)
                s+=random.choice(SUFFIX_AR)
            else:
                s=random.choice(PREFIX_EN)+random.choice(bases)
                if random.random()<0.72: s+=' '+random.choice(MOD_EN)
                if random.random()<0.25: s+=' about '+random.choice(SLOTS_EN)
                s+=random.choice(SUFFIX_EN)
            s=' '.join(s.split())
            seen.add(s)
        if len(seen)<target:
            raise RuntimeError((intent,lang,len(seen)))
        chosen=sorted(seen)[:target]
        texts.extend(chosen); labels.extend([intent]*target)

assert len(texts)==10000
idx=list(range(len(texts))); random.shuffle(idx)
texts=[texts[i] for i in idx]; labels=[labels[i] for i in idx]
norm=[normalize(x) for x in texts]

xtr,xte,ytr,yte=train_test_split(norm,labels,test_size=0.15,random_state=42,stratify=labels)
vec=TfidfVectorizer(ngram_range=(1,2),max_features=3200,min_df=2,sublinear_tf=True,norm='l2',token_pattern=r'(?u)\b\w+\b')
X=vec.fit_transform(xtr); Xt=vec.transform(xte)
clf=SGDClassifier(loss='log_loss',alpha=0.00008,max_iter=120,tol=1e-4,random_state=42,average=True)
clf.fit(X,ytr)
acc=accuracy_score(yte,clf.predict(Xt))

items=sorted(vec.vocabulary_.items(), key=lambda kv: kv[1])
vocab=[k for k,i in items]
assert len(vocab)==len(vec.idf_)
root={
 'name':'Ishrab Adaptive Health NLU',
 'version':'2.0.0',
 'type':'tfidf_logistic_regression_plus_persistent_memory',
 'languages':['ar','en'],
 'classes':list(clf.classes_),
 'vocabulary':vocab,
 'idf':[round(float(x),7) for x in vec.idf_],
 'coefficients':[[round(float(x),7) for x in row] for row in clf.coef_],
 'intercepts':[round(float(x),7) for x in clf.intercept_],
 'training_examples':len(texts),
 'validation_accuracy':round(float(acc),5),
 'intent_count':len(clf.classes_),
 'learning':{
   'persistent_memory':True,
   'online_intent_examples':True,
   'correction_memory':True,
   'language_preferences':True,
   'automatic_forgetting':False
 },
 'glucose_model':{
   'name':'Ishrab Adaptive Glucose Regressor',
   'version':'2.0.0',
   'features':['bias','fasting','before_meal','after_meal','bedtime','sick','carbs','activity','stress','hydration','hour_sin','hour_cos'],
   'seed_weights':[0.45,0.02,0.01,0.12,0.02,0.14,0.22,-0.11,0.10,-0.05,-0.01,0.01],
   'learning_rate':0.025,'l2':0.002
 }
}
out=Path(sys.argv[1] if len(sys.argv)>1 else 'local_health_ai_v2.json')
out.write_text(json.dumps(root,ensure_ascii=False,separators=(',',':')))
Path(str(out)+'.stats.json').write_text(json.dumps({'examples':len(texts),'intents':len(INTENTS),'validation_accuracy':acc,'vocabulary':len(vocab)},indent=2))
print('wrote',out,'bytes',out.stat().st_size,'acc',acc,'vocab',len(vocab),'classes',list(clf.classes_))
