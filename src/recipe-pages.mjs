import fs from 'node:fs';
import path from 'node:path';

const LANGS=['ar','en','fr'];
const FILES=['meals-01.json','meals-02.json','meals-03.json','meals-04.json','healthy-01.json'];
const TEXT={
 ar:{recipes:'الطبخ والوصفات',care:'العناية بالبشرة والجسم',home:'الرئيسية',head:'مطبخ ربح لاب',intro:'مكتبة من 100 وجبة متنوعة و20 وصفة متوازنة، بمقادير فعلية وخطوات تحضير مستقلة. اختَر المطبخ أو المكونات وافتح الوصفة كاملة.',meals:'100 وجبة من مطابخ العالم',healthy:'20 وصفة صحية ومتوازنة',search:'ابحث عن وصفة أو مكوّن',all:'الكل',view:'اطّلع على الوصفة كاملة',count:'وصفة',minutes:'دقيقة',servings:'حصص',ingredients:'المقادير',method:'طريقة التحضير',tip:'تفصيل خاص بهذه الوصفة',safety:'السلامة الغذائية والحساسية',about:'حول الوصفة',legal:'هذه وصفات منزلية تحريرية قابلة للتعديل، ولم تُختبر في مطبخ تجريبي. ليست خططاً علاجية أو قيماً غذائية مخبرية. راقب الحساسية ونظافة الأدوات ودرجات التسوية.',healthNote:'الوصفات الموسومة «متوازنة» تعتمد على التنوع والخضر والحبوب والبقول؛ هذا وصف للمكونات لا ادعاء بأن الطبق يناسب كل حالة صحية.',steps:['حضّر المكونات','ابدأ الطهي','أكمل التسوية','لمسة مميزة','افحص السلامة قبل التقديم'],source:'مرجعان رسميان للسلامة والتوازن الغذائي',tags:{moroccan:'المطبخ المغربي',mediterranean:'المتوسطي',italian:'الإيطالي',french:'الفرنسي',levant:'المشرقي','south-asian':'جنوب آسيا','southeast-asian':'جنوب شرق آسيا','east-asian':'شرق آسيا',african:'الإفريقي',american:'الأمريكي',breakfast:'الفطور',dessert:'الحلويات',healthy:'وجبات متوازنة'},noResults:'لم نجد وصفة مطابقة. جرب مكوناً أو اسماً آخر.',browse:'استكشف المجموعات',measure:'المقادير لحصص تقريبية ويمكن تعديلها وفق الحاجة.',warning:'الطبخ المنزلي يتطلب مقياس حرارة عند تسوية الدواجن واللحوم والأسماك.'},
 en:{recipes:'Cooking & recipes',care:'Skin & body care',home:'Home',head:'The RibhLab kitchen',intro:'100 international meals and 20 balanced recipes with measured ingredients and usable cooking steps. Search by dish, ingredient or cuisine.',meals:'100 meals from around the world',healthy:'20 healthy and balanced recipes',search:'Search dishes or ingredients',all:'All',view:'Read the full recipe',count:'recipes',minutes:'min',servings:'servings',ingredients:'Ingredients',method:'Preparation',tip:'Dish-specific detail',safety:'Food safety and allergens',about:'About this dish',legal:'These are original editorial home-style adaptations, not recipes claimed to have been professionally kitchen-tested. They are not medical meal plans or laboratory nutrient analyses. Check allergies, hygiene and food temperatures.',healthNote:'The balanced label reflects the inclusion of vegetables, legumes and whole grains where suitable; it does not mean a recipe meets every individual dietary need.',steps:['Prepare ingredients','Start cooking','Cook to the right texture','Dish-specific detail','Check safety before serving'],source:'Official safety and balanced-diet references',tags:{moroccan:'Moroccan',mediterranean:'Mediterranean',italian:'Italian',french:'French',levant:'Levantine','south-asian':'South Asian','southeast-asian':'Southeast Asian','east-asian':'East Asian',african:'African',american:'Americas',breakfast:'Breakfast',dessert:'Desserts',healthy:'Balanced meals'},noResults:'No matching recipe. Try another ingredient or dish.',browse:'Explore the collection',measure:'Quantities are for approximate servings and can be adjusted.',warning:'Use a food thermometer where poultry, meat or fish requires safe internal temperatures.'},
 fr:{recipes:'Cuisine & recettes',care:'Soins du corps et de la peau',home:'Accueil',head:'La cuisine RibhLab',intro:'100 plats variés et 20 recettes équilibrées, avec quantités et préparation expliquée. Recherchez par plat, ingrédient ou cuisine.',meals:'100 plats du monde',healthy:'20 recettes saines et équilibrées',search:'Rechercher un plat ou un ingrédient',all:'Tous',view:'Lire la recette complète',count:'recettes',minutes:'min',servings:'portions',ingredients:'Ingrédients',method:'Préparation',tip:'Détail propre à ce plat',safety:'Sécurité alimentaire et allergènes',about:'À propos du plat',legal:'Il s’agit d’adaptations rédactionnelles maison, non de recettes prétendument testées en laboratoire culinaire. Elles ne sont ni des régimes thérapeutiques ni des analyses nutritionnelles. Vérifiez allergies, hygiène et températures.',healthNote:'La mention « équilibrée » décrit notamment la place des légumes, légumineuses et céréales ; elle ne signifie pas que la recette convient à chaque situation médicale.',steps:['Préparer les ingrédients','Commencer la cuisson','Obtenir la bonne texture','Détail de cette recette','Contrôler la sécurité alimentaire'],source:'Références officielles sur la sécurité et l’équilibre alimentaire',tags:{moroccan:'Marocaine',mediterranean:'Méditerranéenne',italian:'Italienne',french:'Française',levant:'Levantine','south-asian':'Asie du Sud','southeast-asian':'Asie du Sud-Est','east-asian':'Asie de l’Est',african:'Africaine',american:'Amériques',breakfast:'Petit-déjeuner',dessert:'Desserts',healthy:'Plats équilibrés'},noResults:'Aucun résultat. Essayez un autre ingrédient ou plat.',browse:'Explorer les collections',measure:'Les quantités correspondent à des portions indicatives et peuvent être adaptées.',warning:'Utilisez un thermomètre alimentaire pour les viandes, volailles et poissons.'}
};
const ACTIONS={
 soup:{
 ar:['قطّع الخضر والعطريات قطعاً متقاربة واترك البقول الجافة تُغسل جيداً؛ استخدم مرقاً أو ماءً نظيفاً بالمقدار المكتوب.','ابدأ بطهي البصل والثوم إن وُجدا في قليل من الدهن المذكور، ثم أضف الخضر والبقول والطماطم والسائل وحرّك مرة.','اترك الحساء يغلي برفق مع التحريك من حين لآخر حتى تنضج البقول والخضر تماماً؛ أضف الأعشاب أو الشعيرية في وقت يناسب سرعة نضجها.'],
 en:['Cut the vegetables and aromatics evenly and rinse dry pulses; measure the listed stock or clean water.','Gently soften onion and garlic if present in the listed oil, then add vegetables, pulses, tomato and liquid. Stir once.','Simmer gently, stirring occasionally, until legumes and vegetables are fully tender; add herbs or noodles according to their cooking time.'],
 fr:['Coupez régulièrement les légumes et aromates, rincez les légumineuses sèches et mesurez le bouillon ou l’eau.','Faites fondre doucement oignon et ail, si présents, dans la matière grasse indiquée puis ajoutez légumes, légumineuses, tomate et liquide.','Laissez mijoter en remuant parfois jusqu’à cuisson complète; incorporez herbes ou nouilles selon leur durée de cuisson.']},
 tagine:{
 ar:['قطّع الخضر وأعدّ التوابل والسائل. إذا استُعمل لحم، أبقه مبرداً إلى حين الطهي وافصل أدواته عن الخضر.','ضع البصل والعطريات مع الدهن في طاجين أو قدر ثقيل، وأضف اللحم إن وُجد ليكتسب لوناً خفيفاً ثم رتب الخضر فوقه.','أضف السائل تدريجياً وغطّ الإناء واطه على نار هادئة حتى يطرى المكوّن الأساسي؛ أضف العناصر سريعة الطهي في المرحلة الأخيرة.'],
 en:['Cut vegetables and measure spices and liquid. Keep raw meat chilled and separate from vegetables until cooking.','Start onion and aromatics with the specified fat in a tagine or heavy covered pot, lightly brown meat if present, then layer vegetables.','Add liquid sparingly, cover and simmer gently until the main ingredients are tender; add quick-cooking items toward the end.'],
 fr:['Coupez les légumes, mesurez épices et liquide. Conservez la viande crue au frais et séparez ses ustensiles.','Faites revenir oignon et aromates dans une cocotte ou un tajine avec la matière grasse prévue; dorez légèrement la viande si présente puis disposez les légumes.','Versez peu à peu le liquide, couvrez et mijotez à feu doux; ajoutez les ingrédients fragiles en fin de cuisson.']},
 stew:{
 ar:['حضّر الخضر والبقول أو اللحم وفق المقادير؛ قطّع المكوّنات بأحجام مناسبة للتسوية المتساوية.','ليّن البصل والثوم إن وُجدا، ثم حمّر اللحم إن وُجد قبل إضافة الطماطم أو المرق والبهارات.','غطّ القدر واتركه على نار هادئة حتى تتماسك الصلصة وتنضج المكونات؛ قلّب برفق وأضف ماءً ساخناً عند الحاجة.'],
 en:['Prepare vegetables, pulses or meat to the listed quantities and cut evenly for uniform cooking.','Soften onion and garlic if included, brown raw meat if present, then introduce tomato, stock and seasonings.','Cover and simmer gently until the ingredients cook through and the sauce reduces; stir occasionally and add warm water only if needed.'],
 fr:['Préparez légumes, légumineuses ou viande aux quantités indiquées et coupez-les régulièrement.','Attendrissez oignon et ail si présents, dorez la viande crue si nécessaire, puis ajoutez tomate, bouillon et épices.','Couvrez et laissez mijoter jusqu’à cuisson complète et réduction de la sauce; remuez doucement et complétez en eau chaude si besoin.']},
 couscous:{
 ar:['اغسل الخضر وقطّعها، وأعدّ الكسكس بالترطيب التدريجي حسب نوع السميد المستخدم.','ابدأ بطهي اللحم أو الخضر القاسية في المرق المتبل، ثم أضف بقية الخضر وفق زمن نضجها.','بخّر الكسكس أو حضّره وفق تعليمات العبوة حتى تتفكك حباته، ثم قدمه مع المرق والخضر المطهوة جيداً.'],
 en:['Wash and chop vegetables and moisten the couscous progressively according to the semolina type.','Start meat or firm vegetables in seasoned stock, then add quicker-cooking vegetables later.','Steam couscous or prepare according to the pack until fluffy, then serve with the fully cooked vegetables and broth.'],
 fr:['Lavez et taillez les légumes et hydratez progressivement la semoule selon son type.','Commencez par la viande ou les légumes fermes dans un bouillon parfumé, puis ajoutez les légumes rapides à cuire.','Faites cuire le couscous à la vapeur ou selon l’emballage pour séparer les grains; servez avec le bouillon et les légumes cuits.']},
 rice:{
 ar:['اغسل الأرز بالماء البارد واتبع تعليمات الصنف؛ اقطع الخضر وأعدّ المكونات الأخرى.','شوّح البصل أو الخضر إن وُجدت، وأضف البروتين النيئ إن استُعمل حتى يتحمّر، ثم ضع الأرز والسائل بالمقدار المناسب للصنف.','غطّ القدر واترك الأرز ينضج على نار هادئة؛ لا تكثر التحريك. اتركه يستريح مغطى بضع دقائق ثم افصل الحبات بالشوكة.'],
 en:['Rinse rice as suitable for the variety and prepare the vegetables and remaining ingredients.','Soften onion or vegetables when included and brown any raw protein, then add rice and its appropriate liquid ratio.','Cover and cook over low heat without frequent stirring; rest briefly off the heat before fluffing with a fork.'],
 fr:['Rincez le riz selon la variété et préparez les légumes et autres ingrédients.','Faites revenir oignon ou légumes si présents, dorez toute protéine crue, puis ajoutez le riz et sa proportion adaptée de liquide.','Couvrez et laissez cuire doucement sans remuer sans cesse; laissez reposer puis aérez les grains avec une fourchette.']},
 pasta:{
 ar:['اغلِ قدراً كبيراً من الماء واطه المعكرونة حتى تصبح مناسبة للقضم؛ احتفظ بكوب صغير من ماء السلق.','حضّر الخضر أو الصلصة في مقلاة مستقلة، وأنضج أي بروتين نيئ تماماً قبل جمعه بالمعكرونة.','صفِّ المعكرونة وقلّبها مع الصلصة وأضف ماء سلق قليلاً عند الحاجة لتصبح متجانسة؛ أضف الأعشاب والجبن قرب التقديم.'],
 en:['Boil pasta in plenty of water until tender but firm; reserve a cup of cooking water.','Prepare vegetables or sauce separately and fully cook any raw protein before combining.','Drain and toss pasta with sauce, adding small splashes of cooking water if needed; finish with herbs or cheese near serving.'],
 fr:['Faites cuire les pâtes dans beaucoup d’eau jusqu’à une texture ferme et tendre; réservez un peu d’eau de cuisson.','Préparez séparément légumes et sauce et cuisez intégralement toute protéine crue.','Égouttez et mélangez les pâtes à la sauce avec un peu d’eau de cuisson; terminez par herbes ou fromage au service.']},
 bake:{
 ar:['سخّن الفرن مسبقاً إلى نحو 190 درجة مئوية ما لم تتطلب طبيعة العجين حرارة أخرى، وجهّز المكونات والحشوة.','شكّل الخليط أو رتب الطبقات في قالب مناسب ومدهون قليلاً عند الحاجة، مع توزيع المكونات بالتساوي.','اخبز حتى يصبح السطح ذهبياً وينضج الوسط؛ يختلف الزمن حسب سمك الطبق والقالب، لذلك تحقق من الداخل قبل التقديم.'],
 en:['Preheat the oven to about 190°C unless the dough requires a different setting; prepare the ingredients and filling.','Shape the mixture or assemble layers in a suitable, lightly greased pan as needed.','Bake until the surface colors and the centre cooks through; exact timing depends on thickness and oven, so check the middle before serving.'],
 fr:['Préchauffez le four vers 190°C sauf indication propre à la pâte; préparez ingrédients et farce.','Façonnez ou montez les couches dans un plat approprié, légèrement huilé si nécessaire.','Faites cuire jusqu’à coloration et cuisson à cœur; adaptez le temps à l’épaisseur du plat et contrôlez le centre.']},
 pancake:{
 ar:['امزج المكونات الجافة، ثم أضف السوائل تدريجياً للحصول على عجينة متجانسة دون مبالغة في العجن.','سخّن مقلاة ثقيلة على نار متوسطة أو هادئة مع مسحة دهن عند الحاجة.','اسكب كمية متشابهة لكل قطعة واطهها حتى تثبت ويصبح لونها مناسباً؛ تأكد من تمام نضج أي بيض في العجين.'],
 en:['Mix dry ingredients, then add liquids gradually to make an even batter or dough without overmixing.','Warm a heavy skillet over medium or gentle heat with a thin film of fat if needed.','Cook similarly sized portions until the centers set and the surfaces color evenly; ensure any egg in the batter cooks fully.'],
 fr:['Mélangez les ingrédients secs puis versez progressivement les liquides pour obtenir une pâte homogène, sans trop travailler.','Chauffez une poêle épaisse à feu moyen ou doux, légèrement graissée si nécessaire.','Cuisez des portions régulières jusqu’à prise complète et coloration; tout œuf présent doit être suffisamment cuit.']},
 salad:{
 ar:['اغسل الخضر جيداً بالماء الجاري وجفف الأوراق؛ اطه الحبوب أو البيض أو البقول النيئة المذكورة قبل استخدامها.','قطّع المكونات إلى قطع متقاربة وجهّز التتبيلة من الزيت والليمون أو الخل بحسب القائمة.','اجمع المكونات برفق وأضف التتبيلة قبل التقديم. احفظ السلطات المحتوية على بيض أو ألبان أو أسماك مبردة.'],
 en:['Wash produce under running water and dry leafy greens; cook any uncooked grains, eggs or pulses listed before use.','Cut ingredients evenly and mix the dressing from the listed oil, citrus or vinegar.','Toss gently and dress shortly before serving; refrigerate salads containing eggs, dairy or fish.'],
 fr:['Lavez soigneusement les légumes et séchez les feuilles; cuisez au préalable céréales, œufs ou légumineuses crus.','Coupez régulièrement et mélangez la vinaigrette avec l’huile, le citron ou le vinaigre prévus.','Assemblez sans écraser et assaisonnez avant service; réfrigérez les salades contenant œufs, laitages ou poisson.']},
 omelet:{
 ar:['اخفق البيض جيداً ونظّف الخضر وقطّعها إلى قطع صغيرة.','شوّح الخضر في مقلاة مناسبة حتى يتبخر ماءها ويبدأ نضجها.','اسكب البيض وخفف الحرارة وغطِّ عند الحاجة حتى تنضج العجة من الداخل؛ لا تترك البيض النيئ سائلاً.'],
 en:['Beat the eggs thoroughly; wash vegetables and cut them into small pieces.','Sauté vegetables in a skillet until excess moisture evaporates and they begin to soften.','Add beaten eggs, lower the heat and cover if needed until the centre is safely set, not runny.'],
 fr:['Battez les œufs et coupez les légumes lavés en petits morceaux.','Faites revenir les légumes pour éliminer l’excès d’eau et les attendrir.','Ajoutez les œufs, baissez le feu et couvrez si nécessaire jusqu’à prise complète du centre.']},
 skillet:{
 ar:['قطّع الخضر والبروتين إلى أحجام متساوية وجهّز الصلصة والتوابل قبل تسخين المقلاة.','حمّر المكون الرئيسي في المقلاة مع الدهن المذكور، ثم أضف الخضر والعطريات بالتدريج.','أكمل على نار معتدلة حتى تنضج المكونات ويصبح قوام الصلصة متجانساً، مع تقليب يقي من الاحتراق.'],
 en:['Cut vegetables and protein evenly; measure sauce and spices before heating the skillet.','Brown the main ingredient with the listed fat, then add aromatics and vegetables in stages.','Continue over moderate heat until the ingredients are cooked through and the sauce has the desired texture, stirring to prevent burning.'],
 fr:['Taillez légumes et protéine régulièrement et mesurez sauce et épices avant de chauffer la poêle.','Dorez l’ingrédient principal avec la matière grasse prévue, puis ajoutez aromates et légumes par étapes.','Poursuivez à feu modéré jusqu’à cuisson complète et consistance voulue en remuant pour éviter de brûler.']},
 grill:{
 ar:['جفف المكون الرئيسي وقطعه بحجم متقارب، وأعدّ التتبيلة بالمكونات المذكورة.','سخّن الشواية أو مقلاة الشواء جيداً واطه البروتين على دفعات دون تزاحم.','قلّب بحذر وأكمل حتى تنضج القطع من الداخل؛ أضف الخضر أو المرافقة المطهوة عند التقديم.'],
 en:['Pat the main ingredient dry, portion evenly and prepare the listed marinade.','Preheat a grill or griddle and cook in batches without overcrowding.','Turn carefully and cook all the way through; serve with prepared vegetables or cooked grains.'],
 fr:['Séchez l’ingrédient principal, taillez-le régulièrement et préparez la marinade indiquée.','Préchauffez le gril ou une poêle-gril et cuisez sans surcharger.','Retournez avec soin et assurez une cuisson à cœur; servez avec légumes ou céréales préparés.']},
 roast:{
 ar:['سخن الفرن مسبقاً نحو 200 درجة مئوية، وقطّع الخضر قطعاً متقاربة مع تجفيف المكونات.','وزّع المكونات على صينية في طبقة واحدة وقلّبها بالدهن والتوابل المكتوبة؛ ابدأ الخضر التي تحتاج زمناً أطول.','اشوِ حتى تلين الخضر وينضج البروتين من الداخل، مع قلب المكونات عند الحاجة لمنع احتراق الأطراف.'],
 en:['Preheat the oven to around 200°C; cut vegetables evenly and pat main ingredients dry.','Spread ingredients in a single layer, coat with listed fat and seasoning and start slow-cooking vegetables first.','Roast until vegetables are tender and any protein is fully cooked; turn pieces as necessary to prevent burning.'],
 fr:['Préchauffez le four vers 200°C; coupez les légumes de façon régulière et séchez les ingrédients.','Étalez sur une plaque sans entasser, enrobez d’huile et d’épices indiquées et commencez par les légumes longs à cuire.','Rôtissez jusqu’à tendreté des légumes et cuisson à cœur des protéines, en retournant au besoin.']},
 curry:{
 ar:['جهز الخضر والبروتين والبهارات والسائل؛ قطّع المكونات قطعاً تسمح بنضج متساوٍ.','ليّن البصل والثوم والزنجبيل إن وُجدت ثم قلّب التوابل قليلاً؛ أضف الطماطم أو حليب جوز الهند والمكونات الرئيسية.','اترك الصلصة تغلي برفق حتى تنضج الخضر والبروتين ويصبح قوامها متجانساً؛ عدّل القوام بالماء الساخن لا بالملح الزائد.'],
 en:['Prepare vegetables, protein, seasonings and liquid, cutting pieces evenly.','Soften onion, garlic and ginger if included; briefly warm spices before adding tomatoes or coconut milk and the main ingredients.','Simmer until vegetables and protein are safely cooked and the sauce comes together; adjust consistency with warm water, not excess salt.'],
 fr:['Préparez légumes, protéine, épices et liquide et coupez des morceaux réguliers.','Faites revenir oignon, ail et gingembre si présents; chauffez brièvement les épices puis ajoutez tomate ou lait de coco et ingrédients principaux.','Laissez mijoter jusqu’à cuisson complète et liaison de la sauce; ajustez la consistance avec un peu d’eau chaude.']},
 stirfry:{
 ar:['اغسل وجفف الخضر وقطّعها رقيقة، وحضّر المكونات المطهوة مسبقاً مثل الأرز أو الشعيرية وفق شروط الحفظ الآمن.','سخّن المقلاة جيداً مع قليل من الزيت واطه أي لحم نيئ أولاً، ثم أضف الخضر بالتدريج لتحافظ على قوامها.','أضف الصلصة في النهاية وقلّب سريعاً حتى تتوزع النكهات وتكتمل التسوية؛ لا تترك الأرز المطهو في حرارة الغرفة.'],
 en:['Wash and dry vegetables, slice thinly and prepare any precooked rice or noodles using safe cooling and storage.','Heat the pan with a little listed oil, cook raw meat first if present, then add vegetables in batches to keep texture.','Add sauce toward the end and toss briskly until everything is hot and cooked; do not leave cooked rice at room temperature.'],
 fr:['Lavez et séchez les légumes, taillez-les finement et préparez tout riz ou nouille déjà cuit selon les règles de conservation.','Chauffez la poêle avec l’huile prévue; cuisez d’abord toute viande crue puis faites sauter les légumes par étapes.','Ajoutez la sauce en fin de cuisson et mélangez rapidement; ne laissez pas du riz cuit à température ambiante.']},
 cold:{
 ar:['اغسل الخضر والفواكه جيداً وجهز الحبوب أو المكونات التي تتطلب طبخاً مسبقاً.','قطّع المكونات وامزج أو لفّ حسب شكل الطبق؛ لا تستعمل أي سمك أو روبيان نيئ في وصفة مصممة بمأكولات بحرية مطهوة.','ضع الطبق في الثلاجة إذا احتوى على ألبان أو بيض أو مأكولات بحرية وقدمه خلال مدة حفظ آمنة.'],
 en:['Wash fruit and vegetables and cook any ingredients that require preparation in advance.','Cut and mix or roll the ingredients to suit the dish; do not substitute raw seafood for seafood the recipe expects fully cooked.','Chill promptly if dairy, egg or seafood is included and serve within safe refrigerated storage times.'],
 fr:['Lavez fruits et légumes et cuisez préalablement les ingrédients qui le nécessitent.','Coupez et mélangez ou roulez selon le plat; ne remplacez pas les fruits de mer cuits par des produits crus.','Réfrigérez rapidement tout plat avec laitages, œufs ou fruits de mer et servez dans des délais de conservation sûrs.']},
 puree:{
 ar:['اغسل الخضر وجهز المكونات، واطه المكونات الرئيسية إذا كانت نيئة قبل الخلط.','اشوِ أو اسلق المكون الرئيسي حسب نوعه حتى يلين تماماً ثم صفِّ السوائل الزائدة.','اهرِس مع الطحينة أو الزيت والليمون حسب القائمة، وأضف الماء تدريجياً للحصول على القوام المرغوب.'],
 en:['Wash produce and cook any raw main ingredients before blending.','Roast or simmer the main ingredient until fully tender, then drain excess liquid.','Mash or blend with the listed tahini, oil and citrus, adding water gradually for the intended consistency.'],
 fr:['Lavez les légumes et cuisez tout ingrédient principal cru avant de mixer.','Rôtissez ou faites mijoter jusqu’à tendreté puis égouttez l’excès de liquide.','Écrasez avec tahini, huile ou citron indiqués en ajoutant progressivement un peu d’eau selon la texture.']},
 steam:{
 ar:['نظف السمك أو الخضر وقطّعها بالتساوي وجهز التوابل والسوائل.','ضع المكونات على شبكة فوق ماء يغلي دون غمرها وغطِّ القدر.','استمر في التبخير حتى ينضج الطعام داخلياً وتصبح الخضر طرية؛ أضف الصلصة والتزيين بعد التسوية.'],
 en:['Clean fish or vegetables, cut evenly and prepare seasonings and liquids.','Arrange ingredients on a rack over simmering water without submerging them; cover.','Steam until the food reaches a safe internal temperature and vegetables are tender, then add sauce and garnish.'],
 fr:['Préparez poisson ou légumes, taillez régulièrement et dosez les assaisonnements.','Disposez sur une grille au-dessus de l’eau frémissante sans immerger les aliments, puis couvrez.','Cuisez jusqu’à température sûre à cœur et légumes tendres, puis ajoutez sauce et garniture.']},
 boil:{
 ar:['حضّر العجينة أو المكونات حسب القائمة واغلِ ماءً في قدر واسع.','شكّل قطعاً متقاربة الحجم أو أضف المكونات إلى الماء على دفعات حتى لا يبرد بشدة.','اطه حتى تلين المكونات من الداخل ثم صفِّها برفق واخلطها بالصلصة المعدة مسبقاً.'],
 en:['Prepare dough or ingredients as listed and bring a large pot of water to the boil.','Shape even pieces or add ingredients in batches so the water does not cool sharply.','Cook until tender throughout, drain gently and combine with the prepared sauce.'],
 fr:['Préparez pâte ou ingrédients selon la liste et faites bouillir une grande casserole d’eau.','Façonnez des pièces régulières ou ajoutez par petites quantités pour éviter de refroidir l’eau.','Cuisez jusqu’à tendreté intérieure, égouttez doucement et mélangez à la sauce préparée.']},
 sandwich:{
 ar:['اغسل وجفف مكونات السلطة وجهز الخبز والمرافقة؛ سخّن الفاصولياء أو البروتين المطهو إن كان الطبق ساخناً.','حضّر الحشوة بعد هرس المكونات أو تقطيعها حسب القوام المطلوب، دون استخدام مواد نيئة غير مأمونة.','سخّن الخبز أو التورتيلا قليلاً إن رغبت، ووزّع الحشوة بالتساوي وقدّمها مباشرة.'],
 en:['Wash and dry salad items and prepare bread and fillings; heat cooked beans or protein if the dish is served warm.','Chop or mash the filling as needed without substituting unsafe raw ingredients.','Warm bread or tortillas briefly if desired, distribute filling evenly and serve promptly.'],
 fr:['Lavez et séchez la garniture végétale, préparez pain et accompagnements et réchauffez les légumineuses si souhaité.','Hachez ou écrasez la farce selon la texture recherchée sans ajout d’aliments crus à risque.','Tiédissez pain ou tortillas si besoin, répartissez la garniture et servez sans attendre.']},
 dessert:{
 ar:['اغسل المكونات أو اطه الأرز حسب الحاجة، وامزج السوائل والمحليات بالمقادير المذكورة.','سخّن الخليط برفق في قدر ثقيل مع تقليب مستمر، خصوصاً إذا احتوى على الحليب أو النشا.','أوقف النار بعد أن يتكثف القوام ويصبح المكون الأساسي ناضجاً، ثم قدمه دافئاً أو برده بسرعة في الثلاجة.'],
 en:['Prepare ingredients and any grains, then measure the listed liquids and sweeteners.','Heat gently in a heavy pan, stirring often, especially for milk or starch-based mixtures.','Stop when the mixture thickens and the main ingredient is cooked; serve warm or chill promptly.'],
 fr:['Préparez les ingrédients et céréales, puis mesurez les liquides et produits sucrants.','Chauffez doucement dans une casserole épaisse en remuant souvent, surtout avec lait ou fécule.','Arrêtez lorsque le mélange épaissit et l’ingrédient principal est cuit; servez tiède ou refroidissez rapidement.']}
};
const SAFE={
 ar:{poultry:'اطه الدجاج أو الديك الرومي حتى 74°C في أكثر جزء سمكاً باستعمال مقياس حرارة.',ground:'تحتاج اللحوم المفرومة إلى 71°C على الأقل.',fish:'يحتاج السمك إلى 63°C أو إلى لحم معتم يتفتت بسهولة.',shellfish:'يُطهى الروبيان حتى يصبح معتماً؛ ويُتخلص من المحار الذي لا يفتح أثناء الطهي.',whole:'للحم القطع الكاملة حد 63°C مع استراحة 3 دقائق وفق جدول السلامة.',eggs:'اطه أطباق البيض حتى نحو 71°C مع تمام التماسك.',base:'اغسل الخضر وافصل النيئ عن المطهو، ولا تترك البقايا القابلة للتلف خارج التبريد لأكثر من ساعتين.',allergen:'المكونات المثيرة للحساسية المحتملة'},
 en:{poultry:'Cook poultry to 74°C / 165°F at the thickest point using a food thermometer.',ground:'Ground meat needs 71°C / 160°F or above.',fish:'Cook fin fish to 63°C / 145°F, or until opaque and easily flaked.',shellfish:'Cook shrimp until opaque and discard clams or mussels that remain closed after cooking.',whole:'Whole cuts of meat require 63°C / 145°F plus a 3-minute rest under official guidance.',eggs:'Cook egg dishes to around 71°C / 160°F and until set.',base:'Wash produce, separate raw and cooked foods and refrigerate perishables within two hours.',allergen:'Potential allergens'},
 fr:{poultry:'Cuisez la volaille à 74°C à cœur en utilisant un thermomètre alimentaire.',ground:'La viande hachée doit atteindre au moins 71°C.',fish:'Cuisez le poisson à 63°C ou jusqu’à chair opaque qui se détache facilement.',shellfish:'Cuisez les crevettes jusqu’à opacité et écartez les coquillages non ouverts après cuisson.',whole:'Les morceaux entiers de viande nécessitent 63°C et 3 minutes de repos selon les recommandations.',eggs:'Cuisez les plats à base d’œufs vers 71°C, jusqu’à prise complète.',base:'Lavez les légumes, séparez cru et cuit et réfrigérez les aliments périssables dans les deux heures.',allergen:'Allergènes possibles'}
};
const ALLERGENS={
 wheat:{ids:['flour','wholeflour','semolina','couscous','bulgur','pasta','spaghetti','bread','wholebread','pita','breadcrumbs'],names:{ar:'القمح والغلوتين',en:'wheat / gluten',fr:'blé / gluten'}},
 egg:{ids:['eggs'],names:{ar:'البيض',en:'egg',fr:'œufs'}},
 milk:{ids:['milk','yogurt','greekyogurt','cream','butter','cheese','feta','mozzarella','parmesan'],names:{ar:'الحليب ومشتقاته',en:'milk / dairy',fr:'lait / produits laitiers'}},
 fish:{ids:['fish','salmon','tuna','fishstock','fishsauce'],names:{ar:'السمك',en:'fish',fr:'poisson'}},
 shell:{ids:['shrimp','squid','mussels'],names:{ar:'الرخويات والقشريات',en:'shellfish / molluscs',fr:'crustacés / mollusques'}},
 soy:{ids:['tofu','soysauce'],names:{ar:'الصويا',en:'soy',fr:'soja'}},
 sesame:{ids:['sesame','tahini'],names:{ar:'السمسم',en:'sesame',fr:'sésame'}},
 nuts:{ids:['walnuts','almonds','raisinnuts'],names:{ar:'المكسرات',en:'tree nuts',fr:'fruits à coque'}},
 peanuts:{ids:['peanuts','peanutbutter'],names:{ar:'الفول السوداني',en:'peanuts',fr:'arachides'}}
};
function load(root){
 const dir=path.join(root,'content','recipes');
 const ingredients=JSON.parse(fs.readFileSync(path.join(dir,'ingredients.json'),'utf8')).ingredients;
 const recipes=FILES.flatMap(file=>JSON.parse(fs.readFileSync(path.join(dir,file),'utf8')).recipes);
 const photoLibrary=JSON.parse(fs.readFileSync(path.join(dir,'photo-library.json'),'utf8'));
 const photos=photoLibrary.photos;
 if(photoLibrary.license!=='Unsplash License'||Object.keys(photos).length<18)throw Error('Verified food photo library is incomplete');
 for(const [key,p] of Object.entries(photos))if(!/^photo-\d+-[a-f0-9]+$/.test(p.photoId)||!p.url?.startsWith('https://images.unsplash.com/'+p.photoId+'?')||!p.source?.startsWith('https://unsplash.com/photos/')||!p.photographer)throw Error('Unverified food photography '+key);
 const slugs=new Set();
 for(const r of recipes){
  if(!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(r.slug)||slugs.has(r.slug))throw Error('Invalid/duplicate recipe: '+r.slug);
  slugs.add(r.slug);
  if(!['meal','healthy'].includes(r.kind)||!ACTIONS[r.method]||!TEXT.ar.tags[r.cuisine])throw Error('Unsupported recipe category/method: '+r.slug);
  if(!Number.isInteger(r.minutes)||r.minutes<5||r.minutes>240||r.ingredients.length<4||r.ingredients.length>14)throw Error('Unusable recipe measures: '+r.slug);
  for(const l of LANGS)if(!r.title[l]||!r.tip[l]||r.tip[l].length<50)throw Error('Incomplete recipe translation '+l+' '+r.slug);
  for(const i of r.ingredients)if(!ingredients[i.id]||!/^[0-9.]+(?:[a-zA-Z]+)$/.test(i.amount))throw Error('Unknown or unmeasured ingredient in '+r.slug+': '+i.id+' '+i.amount);
 }
 if(recipes.filter(r=>r.kind==='meal').length!==100||recipes.filter(r=>r.kind==='healthy').length!==20)throw Error('Recipe publication requires exactly 100 meals and 20 balanced dishes');
 return {ingredients,recipes,photos};
}
function svgFor(r,dist){
 const hash=[...r.slug].reduce((n,c)=>(n*31+c.charCodeAt(0))>>>0,11);
 const palettes=[['#fcdbb2','#e4844f','#9f5a4d'],['#f2d5d0','#d57b77','#784851'],['#dfebba','#82ac76','#537e63'],['#d9e9e6','#67a9a8','#51788a'],['#f4e1b2','#e5a34f','#b46e40'],['#e7ddf5','#a185cf','#665c98']];
 const [a,b,c]=palettes[hash%palettes.length],bits=(hash%5)+4;
 const elements=Array.from({length:bits},(_,i)=>{
  const angle=(2*Math.PI*i/bits)+(hash%13)/10,x=320+Math.cos(angle)*92,y=192+Math.sin(angle)*83,rad=20+(i*13+hash)%16;
  return '<ellipse cx="'+x.toFixed(1)+'" cy="'+y.toFixed(1)+'" rx="'+rad+'" ry="'+Math.round(rad*.65)+'" fill="'+(i%2?b:a)+'" transform="rotate('+(i*46+hash%40)+' '+x+' '+y+')" opacity=".94"/>';
 }).join('');
 return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 400" role="img" aria-label="Original abstract plate illustration for '+r.slug+'"><defs><radialGradient id="bg"><stop stop-color="#fff" /><stop offset="1" stop-color="'+a+'"/></radialGradient><filter id="sh"><feDropShadow dx="0" dy="12" stdDeviation="12" flood-color="#1b3041" flood-opacity=".18"/></filter></defs><rect width="640" height="400" rx="25" fill="url(#bg)"/><ellipse cx="320" cy="218" rx="202" ry="132" fill="#fff" filter="url(#sh)"/><ellipse cx="320" cy="216" rx="173" ry="108" fill="#f6f5ec" stroke="'+c+'" stroke-width="4"/><ellipse cx="320" cy="214" rx="142" ry="91" fill="'+a+'" opacity=".48"/>'+elements+'<circle cx="320" cy="200" r="24" fill="'+c+'" opacity=".75"/><path d="M272 158q48-55 100 0M270 249q50 34 105-1" fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round" opacity=".75"/><path d="M54 70q70-40 150-5M445 339q81 37 140-9" fill="none" stroke="'+b+'" stroke-width="5" stroke-linecap="round" opacity=".35"/></svg>';
}
const UNITS={
 g:{ar:'غ',en:'g',fr:'g'},ml:{ar:'مل',en:'ml',fr:'ml'},l:{ar:'لتر',en:'L',fr:'L'},
 tsp:{ar:'ملعقة صغيرة',en:'tsp',fr:'c. à café'},pc:{ar:'قطعة',en:'piece',fr:'pièce'},pcs:{ar:'قطع',en:'pieces',fr:'pièces'},
 stalks:{ar:'أعواد',en:'stalks',fr:'tiges'},cloves:{ar:'فصوص',en:'cloves',fr:'gousses'},
 clove:{ar:'فص',en:'clove',fr:'gousse'},slices:{ar:'شرائح',en:'slices',fr:'tranches'},sheets:{ar:'رقائق',en:'sheets',fr:'feuilles'}
};
function ingredientText(i,lex,l){
 const m=i.amount.match(/^([0-9.]+)([a-zA-Z]+)$/);
 return (m?m[1]+' '+(UNITS[m[2]]?.[l]||m[2]):i.amount)+' '+lex[i.id][l];
}
function allergens(r,l){
 const ids=new Set(r.ingredients.map(i=>i.id));
 const present=Object.values(ALLERGENS).filter(a=>a.ids.some(id=>ids.has(id))).map(a=>a.names[l]);
 return present.length?present.join(' · '):({ar:'لم تُحدد مسببات شائعة من القائمة؛ افحص جميع عبوات المكونات لتجنب التلامس المتبادل.',en:'No common allergen flagged from the ingredient list; check labels and possible cross-contact.',fr:'Aucun allergène courant détecté dans la liste; vérifiez emballages et contaminations croisées.'})[l];
}
function safety(r,l){
 const ids=new Set(r.ingredients.map(i=>i.id)),s=SAFE[l],out=[];
 if(['chicken','chickenthighs','chickenbreast','turkey'].some(x=>ids.has(x)))out.push(s.poultry);
 if(ids.has('groundbeef'))out.push(s.ground);
 if(['fish','salmon'].some(x=>ids.has(x)))out.push(s.fish);
 if(['shrimp','mussels','squid'].some(x=>ids.has(x)))out.push(s.shellfish);
 if(['beef','lamb'].some(x=>ids.has(x)))out.push(s.whole);
 if(ids.has('eggs'))out.push(s.eggs);
 out.push(s.base);
 return out.join(' ');
}
function head(l,k){return TEXT[l][k]}

// Use verified food photographs by matching cuisine, preparation and principal ingredients.
// A reused stock photo is labelled illustrative; it is never presented as a tested result.
function photoFor(recipe,library){
 const ids=new Set(recipe.ingredients.map(i=>i.id)),slug=recipe.slug;
 let group;
 if(slug.includes('couscous')||slug.includes('rfissa'))group=['couscous','tagineA'];
 else if(slug.includes('pizza'))group=['pizza'];
 else if(slug.includes('risotto')||slug.includes('gnocchi'))group=['risottoA','risottoB'];
 else if(slug.includes('hummus')||slug.includes('baba-ghanoush'))group=['hummusA','hummusB','hummusC'];
 else if(slug.includes('falafel')||slug.includes('patties'))group=['falafel'];
 else if(slug.includes('salmon')||ids.has('salmon'))group=['fishA','fishB'];
 else if(slug.includes('pancake')||slug.includes('baghrir')||slug.includes('msemen')||slug.includes('harcha'))group=['pancake'];
 else if(slug.includes('chocolate')||slug.includes('brownie')||slug.includes('cake'))group=['cake'];
 else if(slug.includes('shakshuka')||slug.includes('kefta')||slug.includes('tagine'))group=['tagineA','tagineB'];
 else if(slug.includes('curry')||['south-asian','southeast-asian'].includes(recipe.cuisine)&&ids.has('coconutmilk'))group=['curryA','curryB','curryC'];
 else if(slug.includes('rice')||['rice','stirfry'].includes(recipe.method))group=['riceA','riceB','curryB'];
 else if(['fish','shrimp','mussels'].some(id=>ids.has(id)))group=['fishA','fishB'];
 else if(['pasta','spaghetti'].some(id=>ids.has(id))||recipe.method==='pasta')group=['pasta','risottoA'];
 else if(recipe.method==='soup')group=['soupA','curryC'];
 else if(recipe.method==='salad'||recipe.method==='cold'||recipe.kind==='healthy'&&['quinoa','bulgur','cucumber','lettuce'].some(id=>ids.has(id)))group=['saladA','saladB','hummusC'];
 else if(recipe.cuisine==='moroccan')group=['tagineA','tagineB','couscous'];
 else if(recipe.cuisine==='levant')group=['hummusC','falafel'];
 else if(['bake','roast','grill'].includes(recipe.method))group=['fishA','tagineA','curryA'];
 else if(recipe.kind==='healthy')group=['saladA','saladB','soupA'];
 else group=['tagineA','curryA','riceA','saladA'];
 const n=[...slug].reduce((a,c)=>(a*31+c.charCodeAt(0))>>>0,7);
 const selected=library[group[n%group.length]];
 if(!selected)throw Error('Missing food photo for recipe '+slug);
 return selected;
}
function recipeImage(r,l,photos,esc,loading='lazy'){
 const p=photoFor(r,photos),alt=({ar:'صورة فوتوغرافية توضيحية لطعام من نفس الفئة، قد لا تطابق الوصفة المنزلية حرفياً: ',en:'Illustrative food photograph of a related dish, not a photograph of the exact tested recipe: ',fr:'Photographie illustrative d’un plat comparable, ne montrant pas exactement la recette : '})[l];
 return '<img data-recipe-photo data-fallback="/assets/recipe-images/'+r.slug+'.svg" src="'+esc(p.url)+'" alt="'+esc(alt+r.title[l])+'" width="640" height="400" loading="'+loading+'" decoding="async" referrerpolicy="no-referrer">';
}

function cards(rows,l,lex,esc,photos){
 const t=TEXT[l];
 return rows.map(r=>{
 const ingredients=r.ingredients.map(i=>lex[i.id][l]).join(' ');
 const image=recipeImage(r,l,photos,esc);
 return '<a class="recipe-card" href="/'+l+'/recipes/'+r.slug+'/" data-recipe-card data-kind="'+r.kind+'" data-cuisine="'+r.cuisine+'" data-search="'+esc((r.title[l]+' '+r.title.en+' '+r.title.ar+' '+r.title.fr+' '+ingredients).toLocaleLowerCase())+'">'+image+'<div class="recipe-card-content"><div class="recipe-tag">'+esc(t.tags[r.kind==='healthy'?'healthy':r.cuisine])+'</div><h3>'+esc(r.title[l])+'</h3><div class="recipe-meta"><span>⏱ '+r.minutes+' '+esc(t.minutes)+'</span><span>🍽 '+r.servings+' '+esc(t.servings)+'</span></div><strong>'+esc(t.view)+' ↗</strong></div></a>';
 }).join('');
}
function recipePage(r,l,lex,page,esc,photos){
 const photo=photoFor(r,photos),featuredImage=recipeImage(r,l,photos,esc,'eager');
 const photoNote=({ar:'صورة طعام توضيحية من Unsplash، وقد تختلف عن الوصفة المذكورة.',en:'Illustrative food photo from Unsplash; the exact recipe may differ.',fr:'Photo culinaire illustrative provenant d’Unsplash ; la recette exacte peut différer.'})[l];
 const t=TEXT[l],label=r.title[l],arr=r.ingredients.map(i=>ingredientText(i,lex,l)),steps=[...ACTIONS[r.method][l],r.tip[l],safety(r,l)];
 const howTo=steps.map((s,i)=>'<li class="recipe-step"><span class="recipe-step-index">'+(i+1)+'</span><div><h3>'+esc(t.steps[i])+'</h3><p>'+esc(s)+'</p></div></li>').join('');
 const list=arr.map(i=>'<li>'+esc(i)+'</li>').join('');
 const kindName=t.tags[r.kind==='healthy'?'healthy':r.cuisine];
 const info='<div class="recipe-facts"><span>⏱ '+r.minutes+' '+esc(t.minutes)+'</span><span>🍽 '+r.servings+' '+esc(t.servings)+'</span><span>🌍 '+esc(kindName)+'</span></div>';
 const references='<p class="recipe-reference">'+esc(t.source)+': <a href="https://www.foodsafety.gov/food-safety-charts/safe-minimum-internal-temperatures" target="_blank" rel="noopener noreferrer external">FoodSafety.gov</a> · <a href="https://www.who.int/news-room/fact-sheets/detail/healthy-diet" target="_blank" rel="noopener noreferrer external">WHO</a></p>';
 const jsonLD={"@context":"https://schema.org","@type":"Recipe",name:label,description:r.tip[l],recipeYield:String(r.servings),totalTime:'PT'+r.minutes+'M',image:'https://ribhlab.github.io/assets/recipe-images/'+r.slug+'.svg',recipeIngredient:arr,recipeInstructions:steps.slice(0,4).map((s,i)=>({"@type":"HowToStep",position:i+1,text:s})),recipeCategory:r.kind==='healthy'?t.healthy:t.meals,recipeCuisine:kindName,author:{"@type":"Organization",name:"RibhLab"}};
 const linked='<script type="application/ld+json">'+JSON.stringify(jsonLD).replace(/</g,'\\u003c')+'</script>';
 const content='<div class="recipe-page"><section class="recipe-detail-hero shell"><nav class="recipe-breadcrumb"><a href="/'+l+'/">'+esc(t.home)+'</a> / <a href="/'+l+'/recipes/">'+esc(t.recipes)+'</a> / '+esc(label)+'</nav><div class="recipe-detail-layout"><div><span class="recipe-kicker">RIBHLAB / KITCHEN</span><h1>'+esc(label)+'</h1><p>'+esc(r.tip[l])+'</p>'+info+'<a class="recipe-back" href="/'+l+'/recipes/'+(r.kind==='healthy'?'healthy/':'meals/')+'">'+esc(t.browse)+' ↗</a></div><div class="recipe-photo-figure">'+featuredImage+'<p class="recipe-photo-credit">'+esc(photoNote)+' <a href="'+esc(photo.source)+'" target="_blank" rel="noopener noreferrer external">'+esc(photo.photographer)+' / Unsplash ↗</a></p></div></div></section><main class="shell recipe-detail-content"><div class="recipe-cols"><section class="recipe-panel"><h2>'+esc(t.ingredients)+'</h2><p>'+esc(t.measure)+'</p><ul class="recipe-ingredient-list">'+list+'</ul></section><section class="recipe-panel"><h2>'+esc(t.method)+'</h2><ol class="recipe-step-list">'+howTo+'</ol></section></div><section class="recipe-alert"><h2>'+esc(t.safety)+'</h2><p>'+esc(safety(r,l))+'</p><p><strong>'+esc(SAFE[l].allergen)+':</strong> '+esc(allergens(r,l))+'</p><p>'+esc(t.legal)+'</p>'+references+'</section><p><a class="recipe-back" href="/'+l+'/recipes/">← '+esc(t.head)+'</a></p></main></div>'+linked+'<script defer src="/assets/recipe-filter.js"></script>';
 page(l,{title:label+' | RibhLab',desc:r.tip[l]+' '+t.measure,route:'/'+l+'/recipes/'+r.slug+'/',content,active:'recipes'});
}
export function renderRecipePages(l,page,esc,root,dist){
 const {ingredients,recipes,photos}=load(root),t=TEXT[l];
 const imageDir=path.join(dist,'assets','recipe-images');fs.mkdirSync(imageDir,{recursive:true});
 // Shared original illustrations are generated once per build; not claimed to be photos.
 if(l==='ar')for(const r of recipes)fs.writeFileSync(path.join(imageDir,r.slug+'.svg'),svgFor(r,dist));
 const meals=recipes.filter(r=>r.kind==='meal'),balanced=recipes.filter(r=>r.kind==='healthy');
 const count=meals.length+balanced.length;
 function directory(kind){
  const chosen=kind==='meal'?meals:kind==='healthy'?balanced:recipes;
  const title=kind==='meal'?t.meals:kind==='healthy'?t.healthy:t.head;
  const route='/'+l+'/recipes/'+(kind==='meal'?'meals/':kind==='healthy'?'healthy/':'');
  const filters=kind==='all'?'<div class="recipe-filter-buttons"><button type="button" data-recipe-filter="all" class="active">'+esc(t.all)+'</button><button type="button" data-recipe-filter="meal">'+esc(t.meals)+'</button><button type="button" data-recipe-filter="healthy">'+esc(t.healthy)+'</button></div>':'';
  const header='<section class="recipe-library-hero"><div class="shell"><span class="recipe-kicker">RIBHLAB / KITCHEN / AR · EN · FR</span><h1>'+esc(title)+'</h1><p>'+esc(kind==='all'?t.intro:kind==='healthy'?t.healthNote:t.intro)+'</p><div class="recipe-hero-stats"><a href="/'+l+'/recipes/meals/"><strong>100</strong><span>'+esc(t.meals)+'</span></a><a href="/'+l+'/recipes/healthy/"><strong>20</strong><span>'+esc(t.healthy)+'</span></a></div></div></section>';
  const nav='<nav class="shell recipe-subnav" aria-label="'+esc(t.browse)+'"><a href="/'+l+'/care/">'+esc(t.care)+'</a><a href="/'+l+'/recipes/">'+esc(t.recipes)+'</a><a href="/'+l+'/recipes/meals/">'+esc(t.meals)+'</a><a href="/'+l+'/recipes/healthy/">'+esc(t.healthy)+'</a></nav>';
  const content='<div class="recipe-page">'+header+nav+'<main class="shell recipe-library"><div class="recipe-search"><label for="recipe-query">'+esc(t.search)+'</label><input id="recipe-query" type="search" autocomplete="off" placeholder="'+esc(t.search)+'" data-recipe-search></div>'+filters+'<p data-recipe-result-count aria-live="polite">'+chosen.length+' '+esc(t.count)+'</p><div class="recipe-grid" data-recipe-list>'+cards(chosen,l,ingredients,esc,photos)+'</div><p data-recipe-empty hidden>'+esc(t.noResults)+'</p><p class="recipe-editorial-note">'+esc(t.legal)+'</p></main></div><script defer src="/assets/recipe-filter.js"></script>';
  page(l,{title:title+' | RibhLab',desc:t.intro,route,content,active:'recipes'});
 }
 directory('all');directory('meal');directory('healthy');
 for(const r of recipes)recipePage(r,l,ingredients,page,esc,photos);
 return {meals:meals.length,healthy:balanced.length,count};
}
