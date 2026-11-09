const buyUrl = 'https://rachidnote.gumroad.com/l/ribhlab-budgetflow-excel-budget-planner';
const previewPath = '/assets/finance/budgetflow-dashboard.jpg';
const price = 12;

export const budgetFlowPath = language => `/${language}/finance/budgetflow-excel-planner/`;

const copy = {
  en: {
    title: 'BudgetFlow | Excel Annual Budget and Savings Planner',
    heading: 'Plan your monthly budget in Excel',
    description: 'See how BudgetFlow tracks income, expenses and savings in one annual Excel workbook. View the dashboard and a worked example before buying.',
    homeLink: 'BudgetFlow personal budget planner for Excel',
    buy: 'Get BudgetFlow on Gumroad',
    format: 'Digital download · English workbook · English, Arabic and French guides',
    imageAlt: 'BudgetFlow dashboard with fictional June 2027 figures, income and spending charts, and month-by-month cash balances',
    imageCaption: 'Actual workbook preview with fictional data. Select the image to see it full size.',
    exampleTitle: 'See what is left after spending and saving',
    exampleIntro: 'In the June 2027 example above, the household records income of $5,100, spending of $2,506 and net savings contributions of $390.',
    labels: ['Income', 'Expenses', 'Net savings', 'Available cash this month'],
    exampleResult: 'The month leaves $2,204 of available cash. Adding that to the $11,055 balance carried from May gives $13,259 of closing cash in June. The dashboard also compares each category with its plan, so you can see where the difference comes from.',
    setupTitle: 'Start your own budget',
    steps: [
      'Choose the year, reporting month and currency label. Enter the cash you have at the start of January, excluding savings.',
      'Enter your monthly income, spending and savings plans on Budget. Record dated movements and categories on Transactions.',
      'Compare plan and actual figures on Dashboard, review flagged entries, and check progress towards your four savings goals.'
    ],
    includedTitle: 'What you download',
    included: [
      'An .xlsx workbook with five sheets, two editable charts, 24 editable category names and space for 2,000 transactions per year.',
      'An optional CSV with 194 fictional transactions, guides in English, Arabic and French, and a license for personal household use.',
      'An empty workbook for your own data. Use one currency per annual file. The currency setting is a display label.'
    ],
    requirements: 'The workbook uses manual entry and standard spreadsheet formulas. Obtain Excel separately and check the application testing details on Gumroad before purchasing.',
    seller: 'RibhLab created and sells BudgetFlow. Gumroad handles checkout and download delivery.'
  },
  fr: {
    title: 'BudgetFlow | Budget annuel et épargne sur Excel',
    heading: 'Préparer son budget mensuel sur Excel',
    description: 'Découvrez BudgetFlow, un classeur Excel de suivi annuel des revenus, des dépenses et de l’épargne. Consultez le tableau de bord et un exemple chiffré.',
    homeLink: 'BudgetFlow, modèle Excel de budget personnel',
    buy: 'Acheter BudgetFlow sur Gumroad',
    format: 'Téléchargement numérique · Classeur en anglais · Guides en français, anglais et arabe',
    imageAlt: 'Tableau de bord BudgetFlow avec les chiffres fictifs de juin 2027, les graphiques et les soldes mensuels',
    imageCaption: 'Aperçu du classeur avec des données fictives. Ouvrez l’image pour la consulter en grand.',
    exampleTitle: 'Calculer le reste disponible après dépenses et épargne',
    exampleIntro: 'Dans l’exemple de juin 2027, le foyer enregistre 5 100 USD de revenus, 2 506 USD de dépenses et 390 USD de versements nets à l’épargne.',
    labels: ['Revenus', 'Dépenses', 'Épargne nette', 'Disponible du mois'],
    exampleResult: 'Le disponible du mois est de 2 204 USD. En l’ajoutant au solde de 11 055 USD reporté de mai, on obtient 13 259 USD en fin juin. Le tableau de bord compare aussi les montants réels au budget de chaque catégorie pour expliquer les écarts.',
    setupTitle: 'Commencer son propre budget',
    steps: [
      'Choisissez l’année, le mois et le libellé de la devise. Saisissez la trésorerie disponible début janvier, hors épargne.',
      'Indiquez vos prévisions mensuelles dans Budget. Saisissez les mouvements datés et leur catégorie dans Transactions.',
      'Comparez le budget et le réel dans Dashboard, corrigez les lignes signalées et suivez vos quatre objectifs d’épargne.'
    ],
    includedTitle: 'Contenu du téléchargement',
    included: [
      'Un classeur .xlsx de cinq onglets, deux graphiques modifiables, 24 noms de catégories personnalisables et 2 000 lignes de transactions par an.',
      'Un CSV facultatif de 194 transactions fictives, trois guides en français, anglais et arabe, et une licence personnelle pour un foyer.',
      'Un classeur vierge à remplir avec vos données. Utilisez une devise par fichier annuel. Le paramètre de devise sert à l’affichage.'
    ],
    requirements: 'Le classeur fonctionne avec une saisie manuelle et des formules de tableur. Prévoyez Excel séparément et consultez la fiche Gumroad pour connaître les environnements de test.',
    seller: 'RibhLab a créé et vend BudgetFlow. Gumroad gère le paiement et la livraison du fichier.'
  },
  ar: {
    title: 'BudgetFlow | قالب الميزانية السنوية والادخار في Excel',
    heading: 'خطّط لميزانيتك الشهرية في Excel',
    description: 'اطّلع على قالب BudgetFlow لتنظيم الدخل والمصاريف والادخار في ملف Excel سنوي، مع صورة من لوحة التحكم ومثال بالأرقام.',
    homeLink: 'BudgetFlow لتنظيم الميزانية الشخصية في Excel',
    buy: 'اشترِ BudgetFlow على Gumroad',
    format: 'تحميل رقمي · واجهة الملف بالإنجليزية · أدلة بالعربية والإنجليزية والفرنسية',
    imageAlt: 'لوحة BudgetFlow تعرض مثال يونيو 2027 ببيانات خيالية ورسوم الدخل والمصاريف والأرصدة الشهرية',
    imageCaption: 'معاينة من الملف الفعلي ببيانات خيالية. افتح الصورة لقراءتها بالحجم الكامل.',
    exampleTitle: 'احسب ما تبقّى بعد المصاريف والادخار',
    exampleIntro: 'في مثال يونيو 2027، سجّلت الأسرة دخلاً قدره 5,100 دولار ومصاريف قدرها 2,506 دولارات وصافي ادخار قدره 390 دولاراً.',
    labels: ['الدخل', 'المصاريف', 'صافي الادخار', 'المتاح خلال الشهر'],
    exampleResult: 'المتاح خلال الشهر هو 2,204 دولارات. بإضافته إلى الرصيد المرحّل من مايو، وقدره 11,055 دولاراً، يصبح رصيد نهاية يونيو 13,259 دولاراً. وتقارن اللوحة بين الفعلي والمخطط لكل فئة لتحديد مصدر الفرق.',
    setupTitle: 'ابدأ ميزانيتك الخاصة',
    steps: [
      'اختر السنة والشهر واسم العملة، ثم أدخل رصيد بداية يناير المتاح للمصاريف، باستثناء الادخار.',
      'ضع خطتك الشهرية في ورقة Budget، وسجّل تاريخ كل حركة وفئتها ومبلغها في Transactions.',
      'راجع الفرق بين المخطط والفعلي في Dashboard، وصحّح السطور المشار إليها، وتابع أهداف الادخار الأربعة.'
    ],
    includedTitle: 'محتويات التحميل',
    included: [
      'ملف بصيغة ‎.xlsx‎ من خمس أوراق، ورسمان قابلان للتعديل، و24 اسماً للفئات قابلة للتخصيص، وسعة 2,000 حركة في السنة.',
      'ملف CSV اختياري فيه 194 حركة خيالية، وثلاثة أدلة بالعربية والإنجليزية والفرنسية، ورخصة للاستخدام الشخصي داخل الأسرة.',
      'نسخة فارغة لتسجيل بياناتك. استعمل عملة واحدة لكل ملف سنوي. إعداد العملة يغيّر اسمها في العرض.'
    ],
    requirements: 'يعتمد الملف على الإدخال اليدوي وصيغ الجداول. تحتاج إلى Excel بشكل منفصل، وتجد تفاصيل الاختبارات في صفحة Gumroad قبل الشراء.',
    seller: 'أعدّ RibhLab قالب BudgetFlow ويبيعه. يتولّى Gumroad الدفع وتسليم الملف.'
  }
};

export const budgetFlowLinkLabel = language => copy[language].homeLink;

export function renderBudgetFlowPage(language, page, escape, domain) {
  const words = copy[language];
  const route = budgetFlowPath(language);
  const previewUrl = domain + previewPath;
  const money = new Intl.NumberFormat(language, {
    style: 'currency', currency: 'USD', maximumFractionDigits: 0
  });
  const list = items => items.map(item => `<li>${escape(item)}</li>`).join('');
  const button = `<a class="budgetflow-buy" href="${buyUrl}">${escape(words.buy)} <bdi>${escape(money.format(price))}</bdi></a>`;
  const example = [5100, 2506, 390, 2204].map((amount, index) => `
    <div><dt>${escape(words.labels[index])}</dt><dd><bdi>${escape(money.format(amount))}</bdi></dd></div>
  `).join('');
  const product = {
    '@context': 'https://schema.org',
    '@type': 'Product',
    name: 'RibhLab BudgetFlow',
    description: words.description,
    image: previewUrl,
    brand: {'@type': 'Brand', name: 'RibhLab'},
    offers: {'@type': 'Offer', price, priceCurrency: 'USD', url: buyUrl}
  };
  const productJson = JSON.stringify(product).replace(/</g, '\\u003c');

  page(language, {
    title: words.title,
    desc: words.description,
    route,
    socialImage: previewUrl,
    socialAlt: words.imageAlt,
    content: `
      <link rel="stylesheet" href="/assets/budgetflow.css">
      <script type="application/ld+json">${productJson}</script>
      <div class="shell budgetflow-page">
        <section class="budgetflow-hero" aria-labelledby="budgetflow-title">
          <div class="budgetflow-intro">
            <p class="budgetflow-brand">RibhLab · BudgetFlow</p>
            <h1 id="budgetflow-title">${escape(words.heading)}</h1>
            <p class="budgetflow-lead">${escape(words.description)}</p>
            ${button}
            <p class="budgetflow-format">${escape(words.format)}</p>
          </div>
          <figure>
            <a href="${previewPath}"><img src="${previewPath}" alt="${escape(words.imageAlt)}" width="1440" height="1556" decoding="async" fetchpriority="high"></a>
            <figcaption>${escape(words.imageCaption)}</figcaption>
          </figure>
        </section>
        <section class="budgetflow-panel" aria-labelledby="budgetflow-example">
          <h2 id="budgetflow-example">${escape(words.exampleTitle)}</h2>
          <p>${escape(words.exampleIntro)}</p>
          <dl class="budgetflow-example">${example}</dl>
          <p>${escape(words.exampleResult)}</p>
        </section>
        <div class="budgetflow-details">
          <section class="budgetflow-panel">
            <h2>${escape(words.setupTitle)}</h2>
            <ol>${list(words.steps)}</ol>
          </section>
          <section class="budgetflow-panel">
            <h2>${escape(words.includedTitle)}</h2>
            <ul>${list(words.included)}</ul>
            <p>${escape(words.requirements)}</p>
          </section>
        </div>
        <div class="budgetflow-checkout">
          ${button}
          <p>${escape(words.seller)}</p>
        </div>
      </div>`
  });
}
