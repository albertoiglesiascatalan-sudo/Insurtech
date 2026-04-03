export type BakeryCategory = "artesanal" | "bollos" | "especial" | "molde";

export interface BakeryProduct {
  slug: string;
  name: string;
  description: string;
  longDescription: string;
  price: number;
  unit: string;
  category: BakeryCategory;
  emoji: string;
  gradient: string;
  ingredients: string[];
  allergens: string[];
  weight: string;
  available: boolean;
  featured: boolean;
  tags: string[];
}

export const CATEGORY_LABELS: Record<BakeryCategory, string> = {
  artesanal: "Panes Artesanales",
  bollos: "Bollería",
  especial: "Panes Especiales",
  molde: "Panes de Molde",
};

export const CATEGORY_COLORS: Record<BakeryCategory, string> = {
  artesanal: "bg-amber-100 text-amber-800",
  bollos: "bg-orange-100 text-orange-800",
  especial: "bg-rose-100 text-rose-800",
  molde: "bg-yellow-100 text-yellow-800",
};

export const BAKERY_PRODUCTS: BakeryProduct[] = [
  {
    slug: "pan-masa-madre",
    name: "Pan de Masa Madre",
    description: "Fermentado 24 horas, corteza crujiente y miga alveolada.",
    longDescription:
      "Nuestro pan de masa madre es el resultado de 24 horas de fermentación lenta con nuestra cepa de levadura natural que cuidamos desde hace más de 10 años. Corteza dorada y crujiente, miga abierta y alveolada con un sabor ligeramente ácido que lo hace inconfundible. Sin levadura industrial, sin aditivos.",
    price: 4.5,
    unit: "hogaza",
    category: "artesanal",
    emoji: "🍞",
    gradient: "from-amber-200 to-orange-300",
    ingredients: ["Harina de trigo T80", "Agua", "Sal marina", "Masa madre"],
    allergens: ["Gluten"],
    weight: "800 g",
    available: true,
    featured: true,
    tags: ["sin levadura industrial", "fermentación lenta", "artesanal"],
  },
  {
    slug: "baguette-tradicional",
    name: "Baguette Tradicional",
    description: "Receta clásica francesa, crujiente por fuera y esponjosa por dentro.",
    longDescription:
      "Elaborada siguiendo la tradición francesa con harina de fuerza, agua, sal y levadura fresca. Horneada dos veces para conseguir esa corteza imposiblemente crujiente y una miga esponjosa y aromática. Perfecta para bocadillos, tostadas o simplemente con mantequilla.",
    price: 1.8,
    unit: "unidad",
    category: "artesanal",
    emoji: "🥖",
    gradient: "from-yellow-200 to-amber-300",
    ingredients: ["Harina de trigo", "Agua", "Sal", "Levadura fresca"],
    allergens: ["Gluten"],
    weight: "250 g",
    available: true,
    featured: true,
    tags: ["clásico", "francés", "diario"],
  },
  {
    slug: "pan-centeno",
    name: "Pan de Centeno",
    description: "100% centeno, denso y nutritivo con semillas de alcaravea.",
    longDescription:
      "Elaborado con harina de centeno integral al 100%, este pan oscuro y aromático es uno de los más nutritivos de nuestra tienda. Enriquecido con semillas de alcaravea que le dan un toque herbal inconfundible. Ideal para tostadas con aguacate, salmón ahumado o queso de cabra.",
    price: 3.9,
    unit: "hogaza",
    category: "especial",
    emoji: "🫓",
    gradient: "from-stone-300 to-amber-400",
    ingredients: ["Harina de centeno integral", "Agua", "Sal", "Semillas de alcaravea", "Masa madre de centeno"],
    allergens: ["Gluten"],
    weight: "700 g",
    available: true,
    featured: false,
    tags: ["integral", "sin trigo", "nutritivo"],
  },
  {
    slug: "pan-integral-espelta",
    name: "Pan Integral de Espelta",
    description: "Espelta ecológica, rico en fibra y con un sabor suave y dulzón.",
    longDescription:
      "La espelta es un cereal ancestral con un perfil nutricional superior al trigo moderno. Este pan se elabora con harina de espelta integral ecológica certificada, aportando un sabor ligeramente dulzón y una textura suave. Alto contenido en fibra y minerales. Perfecto para el desayuno.",
    price: 4.2,
    unit: "hogaza",
    category: "especial",
    emoji: "🌾",
    gradient: "from-lime-200 to-green-300",
    ingredients: ["Harina de espelta integral ecológica", "Agua", "Sal", "Levadura fresca"],
    allergens: ["Gluten"],
    weight: "750 g",
    available: true,
    featured: true,
    tags: ["ecológico", "integral", "espelta"],
  },
  {
    slug: "focaccia-romero",
    name: "Focaccia de Romero",
    description: "Esponjosa focaccia italiana con romero fresco y aceite de oliva virgen extra.",
    longDescription:
      "Receta italiana auténtica con una masa de alta hidratación que reposa 18 horas en frío para desarrollar todo su sabor. Generosa en aceite de oliva virgen extra, coronada con romero fresco del huerto y sal en escamas. Lista para disfrutar sola, con embutidos o como base de una bruschetta.",
    price: 5.0,
    unit: "pieza",
    category: "especial",
    emoji: "🫒",
    gradient: "from-green-200 to-emerald-300",
    ingredients: ["Harina de fuerza", "Agua", "Aceite de oliva virgen extra", "Sal en escamas", "Romero fresco", "Levadura"],
    allergens: ["Gluten"],
    weight: "600 g",
    available: true,
    featured: true,
    tags: ["italiano", "aceite oliva", "aromático"],
  },
  {
    slug: "croissant-mantequilla",
    name: "Croissant de Mantequilla",
    description: "Laminado a mano con mantequilla francesa AOP, hojaldrado y dorado.",
    longDescription:
      "El mejor croissant que puedas imaginar, elaborado con mantequilla francesa AOP de alta calidad. Proceso de laminado a mano con 27 capas de mantequilla que crean esa textura hojaldrada única. Crujiente por fuera, tierno y mantecoso por dentro. Recién horneado cada mañana.",
    price: 2.2,
    unit: "unidad",
    category: "bollos",
    emoji: "🥐",
    gradient: "from-yellow-100 to-amber-200",
    ingredients: ["Harina de fuerza", "Mantequilla francesa AOP", "Azúcar", "Sal", "Leche", "Levadura fresca"],
    allergens: ["Gluten", "Lácteos", "Huevo"],
    weight: "90 g",
    available: true,
    featured: true,
    tags: ["bollería", "mantequilla", "hojaldrado"],
  },
  {
    slug: "pan-nueces-pasas",
    name: "Pan de Nueces y Pasas",
    description: "Masa madre con nueces de Castilla y pasas Sultanas, perfecto para el queso.",
    longDescription:
      "Una combinación clásica de panadería artesanal que nunca falla. Masa madre de trigo con nueces de Castilla tostadas y pasas Sultanas que aportan un dulzor natural sin necesidad de azúcar añadido. La combinación ideal para una tabla de quesos o simplemente tostado con mantequilla.",
    price: 5.5,
    unit: "hogaza",
    category: "artesanal",
    emoji: "🫘",
    gradient: "from-amber-300 to-orange-400",
    ingredients: ["Harina T65", "Agua", "Nueces de Castilla", "Pasas Sultanas", "Sal", "Masa madre"],
    allergens: ["Gluten", "Frutos secos"],
    weight: "850 g",
    available: true,
    featured: false,
    tags: ["frutas secas", "masa madre", "quesos"],
  },
  {
    slug: "pan-molde-artesanal",
    name: "Pan de Molde Artesanal",
    description: "Sin conservantes ni aditivos, tierno y suave para toda la semana.",
    longDescription:
      "Olvídate del pan de molde industrial. Este se elabora con harina de trigo, leche, mantequilla, huevo y una pizca de miel para conseguir esa textura tierna y ese sabor casero que tanto se echa de menos. Sin conservantes, sin mejorantes. Aguanta perfectamente 5 días en su bolsa de papel.",
    price: 3.8,
    unit: "pieza",
    category: "molde",
    emoji: "🍞",
    gradient: "from-orange-100 to-amber-200",
    ingredients: ["Harina de trigo", "Leche", "Mantequilla", "Huevo", "Azúcar", "Sal", "Miel", "Levadura"],
    allergens: ["Gluten", "Lácteos", "Huevo"],
    weight: "500 g",
    available: true,
    featured: false,
    tags: ["familiar", "sin aditivos", "tierno"],
  },
  {
    slug: "bagel-clasico",
    name: "Bagel Clásico",
    description: "Escaldado en agua con miel antes del horneado, auténtico estilo Nueva York.",
    longDescription:
      "El auténtico bagel de Nueva York requiere un proceso de escaldado en agua con miel antes de hornear que le da esa corteza brillante y masticable única. Elaborado con harina de fuerza, malta y levadura fresca. Perfecto para rellenar con queso crema y salmón o como más te guste.",
    price: 2.8,
    unit: "unidad",
    category: "bollos",
    emoji: "🥯",
    gradient: "from-amber-200 to-yellow-300",
    ingredients: ["Harina de fuerza", "Malta de cebada", "Agua", "Sal", "Miel", "Levadura"],
    allergens: ["Gluten"],
    weight: "110 g",
    available: true,
    featured: false,
    tags: ["americano", "escaldado", "clásico"],
  },
  {
    slug: "pan-multicereales",
    name: "Pan Multicereales",
    description: "Semillas de sésamo, amapola, girasol y lino. Un clásico saludable.",
    longDescription:
      "Un pan lleno de vida con siete variedades de cereales y semillas: trigo, centeno, cebada, avena, semillas de sésamo, amapola y girasol. La combinación perfecta para quien busca un pan nutritivo, sabroso y con textura. Tostado está extraordinario.",
    price: 4.0,
    unit: "hogaza",
    category: "especial",
    emoji: "🌻",
    gradient: "from-yellow-200 to-lime-300",
    ingredients: ["Harina integral de trigo", "Harina de centeno", "Semillas de sésamo", "Semillas de amapola", "Pipas de girasol", "Semillas de lino", "Sal", "Levadura"],
    allergens: ["Gluten", "Sésamo"],
    weight: "800 g",
    available: true,
    featured: false,
    tags: ["semillas", "nutritivo", "integral"],
  },
  {
    slug: "muffin-arandanos",
    name: "Muffin de Arándanos",
    description: "Esponjoso muffin americano repleto de arándanos frescos.",
    longDescription:
      "Receta americana clásica con arándanos frescos de temporada integrados en una masa esponjosa y húmeda. Cúpula perfecta, ligeramente crujiente por fuera y tierna por dentro. Horneados cada mañana. Un desayuno o merienda perfecta.",
    price: 2.5,
    unit: "unidad",
    category: "bollos",
    emoji: "🫐",
    gradient: "from-violet-200 to-purple-300",
    ingredients: ["Harina", "Azúcar", "Mantequilla", "Huevo", "Leche", "Arándanos frescos", "Levadura química"],
    allergens: ["Gluten", "Lácteos", "Huevo"],
    weight: "120 g",
    available: true,
    featured: false,
    tags: ["bollería", "frutas", "desayuno"],
  },
  {
    slug: "pan-sin-gluten",
    name: "Pan Sin Gluten",
    description: "Elaborado en obrador certificado sin gluten, para celíacos sin compromisos.",
    longDescription:
      "Elaborado en un obrador completamente libre de gluten, certificado por FACE (Federación de Asociaciones de Celíacos de España). Mezcla de harinas de arroz, tapioca y maíz que logra una textura y sabor muy cercanos al pan de trigo tradicional. Apto para celíacos e intolerantes al gluten.",
    price: 5.2,
    unit: "hogaza",
    category: "molde",
    emoji: "✨",
    gradient: "from-sky-200 to-blue-300",
    ingredients: ["Harina de arroz", "Almidón de tapioca", "Harina de maíz", "Agua", "Aceite de girasol", "Sal", "Levadura"],
    allergens: ["Sin gluten"],
    weight: "500 g",
    available: true,
    featured: false,
    tags: ["sin gluten", "celíacos", "certificado"],
  },
];

export function getProduct(slug: string): BakeryProduct | undefined {
  return BAKERY_PRODUCTS.find((p) => p.slug === slug);
}

export function getFeaturedProducts(): BakeryProduct[] {
  return BAKERY_PRODUCTS.filter((p) => p.featured);
}

export function getProductsByCategory(category: BakeryCategory): BakeryProduct[] {
  return BAKERY_PRODUCTS.filter((p) => p.category === category);
}
