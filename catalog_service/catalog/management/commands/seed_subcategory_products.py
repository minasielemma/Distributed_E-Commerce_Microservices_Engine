import uuid
from decimal import Decimal
from django.core.management.base import BaseCommand
from catalog.models import Category, Product, ProductPrice, ProductImage

KADOSH_TENANT_ID = uuid.UUID('6cd2586e-1a03-4833-913f-598596f51732')

SUBCATEGORY_PRODUCTS = {
    'smartphones-mobile-devices': [
        {
            'name': 'Apex Pro 5G Smartphone 256GB',
            'description': 'Flagship 5G smartphone featuring a 6.7-inch OLED display, triple camera system, and ultra-fast charging.',
            'price': Decimal('899.99'),
            'image_url': 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Lumina Fold V2 Dual-Screen Phone',
            'description': 'Next-gen foldable smartphone with dual OLED panels, 12GB RAM, and 512GB storage for seamless multitasking.',
            'price': Decimal('1299.99'),
            'image_url': 'https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'laptops-computers': [
        {
            'name': 'UltraBook Pro 15-inch M3 Chip',
            'description': 'High-performance lightweight laptop with 16GB unified memory, 1TB SSD, and 18-hour battery life.',
            'price': Decimal('1499.00'),
            'image_url': 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Titan Gaming Laptop RTX 4080',
            'description': 'Powerful gaming laptop with Intel i9, NVIDIA RTX 4080, 32GB DDR5 RAM, and 240Hz QHD display.',
            'price': Decimal('2199.99'),
            'image_url': 'https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'audio-headphones': [
        {
            'name': 'SoundMaster Wireless ANC Headphones',
            'description': 'Over-ear studio quality headphones with active noise cancellation, transparency mode, and 40h battery.',
            'price': Decimal('249.99'),
            'image_url': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'PulseFit True Wireless Earbuds',
            'description': 'IPX7 waterproof wireless earbuds with deep bass boost, spatial audio, and wireless charging case.',
            'price': Decimal('129.50'),
            'image_url': 'https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'cameras-photography': [
        {
            'name': 'AeroSight 4K Mirrorless Camera',
            'description': 'Compact full-frame mirrorless camera with 45MP sensor, 8K video recording, and 5-axis IBIS.',
            'price': Decimal('1899.00'),
            'image_url': 'https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'ProLens 50mm f/1.4 Prime Lens',
            'description': 'Ultra-fast 50mm prime lens delivering razor-sharp image quality and stunning creamy bokeh.',
            'price': Decimal('649.99'),
            'image_url': 'https://images.unsplash.com/photo-1617005082133-548c4dd27f35?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'wearable-technology': [
        {
            'name': 'ChronoFit Pro Smartwatch',
            'description': 'Advanced health & fitness tracking smartwatch with heart rate monitoring, ECG, GPS, and OLED display.',
            'price': Decimal('299.99'),
            'image_url': 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Aura Smart Wellness Ring',
            'description': 'Sleek titanium smart ring tracking sleep stages, body temperature, HRV, and daily activity levels.',
            'price': Decimal('279.00'),
            'image_url': 'https://images.unsplash.com/photo-1579586337278-3befd40fd17a?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'electronics-accessories': [
        {
            'name': 'OmniCharge 100W GaN Fast Charger',
            'description': 'Compact 4-port USB-C fast charging hub powered by GaN technology for laptops, phones, and tablets.',
            'price': Decimal('69.99'),
            'image_url': 'https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'MagFlex Magnetic Wireless Power Bank 10000mAh',
            'description': 'Ultra-slim magnetic wireless battery pack with pass-through charging and LED power display.',
            'price': Decimal('49.99'),
            'image_url': 'https://images.unsplash.com/photo-1609592424009-dd279024f2e5?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'mens-clothing': [
        {
            'name': 'Classic Tailored Navy Wool Suit',
            'description': '100% Italian wool two-piece suit with a modern slim fit, notch lapel, and lined jacket.',
            'price': Decimal('349.99'),
            'image_url': 'https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Casual Cotton Oxford Shirt',
            'description': 'Breathable 100% premium cotton button-down shirt ideal for office wear and casual weekends.',
            'price': Decimal('54.99'),
            'image_url': 'https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'womens-clothing': [
        {
            'name': 'Elegance Floral Midi Wrap Dress',
            'description': 'Beautiful lightweight chiffon wrap dress featuring a botanical floral print and v-neckline.',
            'price': Decimal('79.99'),
            'image_url': 'https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Cozy Cashmere Blend Oversized Sweater',
            'description': 'Luxuriously soft knit sweater crafted from sustainable cashmere and merino wool blend.',
            'price': Decimal('119.00'),
            'image_url': 'https://images.unsplash.com/photo-1576995853123-5a10305d93c0?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'kids-baby-clothing': [
        {
            'name': 'Organic Cotton Baby Onesie Set (Pack of 5)',
            'description': 'Hypoallergenic 100% organic cotton onesies with easy snap buttons for infants 0-12 months.',
            'price': Decimal('32.99'),
            'image_url': 'https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Kids Waterproof Hooded Raincoat',
            'description': 'Fun brightly-colored waterproof rain jacket with reflective safety strips and warm fleece lining.',
            'price': Decimal('44.50'),
            'image_url': 'https://images.unsplash.com/photo-1622290291468-a28f7a7dc6a8?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'shoes-footwear': [
        {
            'name': 'Velocity Air Running Sneakers',
            'description': 'Ergonomic performance running shoes with breathable mesh upper and responsive foam cushioning.',
            'price': Decimal('129.99'),
            'image_url': 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Handcrafted Full-Grain Leather Boots',
            'description': 'Durable Goodyear-welted leather ankle boots built for style, comfort, and longevity.',
            'price': Decimal('189.00'),
            'image_url': 'https://images.unsplash.com/photo-1608256246200-53e635b5b65f?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'bags-luggage': [
        {
            'name': 'Executive Leather Laptop Backpack',
            'description': 'Premium full-grain leather backpack with padded 15.6" laptop compartment and anti-theft pocket.',
            'price': Decimal('159.99'),
            'image_url': 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Voyager Polycarbonate Hardside Spinner Suitcase',
            'description': 'Lightweight scratch-resistant carry-on luggage with 360-degree dual spinner wheels and TSA lock.',
            'price': Decimal('139.50'),
            'image_url': 'https://images.unsplash.com/photo-1565026057447-b8899f2911a8?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'jewelry-watches': [
        {
            'name': 'Minimalist Gold Automatic Mesh Watch',
            'description': 'Elegant 40mm stainless steel wristwatch with Japanese automatic movement and sapphire glass.',
            'price': Decimal('219.00'),
            'image_url': 'https://images.unsplash.com/photo-1524805444758-089113d48a6d?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Sterling Silver Cubic Zirconia Pendant Necklace',
            'description': 'Sparkling 925 sterling silver solitaire pendant necklace on an 18-inch adjustable chain.',
            'price': Decimal('69.99'),
            'image_url': 'https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'furniture': [
        {
            'name': 'Modern Ergonomic Mesh Office Chair',
            'description': 'Adjustable lumbar support, 3D armrests, and breathable mesh backrest for all-day comfort.',
            'price': Decimal('249.99'),
            'image_url': 'https://images.unsplash.com/photo-1580481072645-022f9a6d83d0?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Nordic Solid Oak Dining Table',
            'description': 'Scandinavian style 6-seater dining table crafted from solid kiln-dried oak wood.',
            'price': Decimal('599.00'),
            'image_url': 'https://images.unsplash.com/photo-1615066390971-03e4e1c36ddf?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'home-decor': [
        {
            'name': 'Handmade Ceramic Flower Vase Set',
            'description': 'Set of 3 minimalist matte ceramic vases perfect for pampas grass and dried floral arrangements.',
            'price': Decimal('45.00'),
            'image_url': 'https://images.unsplash.com/photo-1578500494198-246f612d3b3d?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Abstract Canvas Wall Art 3-Piece',
            'description': 'Framed modern abstract canvas art prints in neutral beige and gold foil accents.',
            'price': Decimal('89.99'),
            'image_url': 'https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'kitchenware-appliances': [
        {
            'name': 'Smart Touch Air Fryer 5.8 Quart',
            'description': 'Digital touch screen air fryer with 8 preset cooking functions, non-stick basket, and recipe book.',
            'price': Decimal('99.99'),
            'image_url': 'https://images.unsplash.com/photo-1585515320310-259814833e62?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Professional Stainless Steel Cookware Set (10-Piece)',
            'description': 'Tri-ply clad stainless steel pots and pans set compatible with induction cooktops.',
            'price': Decimal('279.00'),
            'image_url': 'https://images.unsplash.com/photo-1584992236310-6edddc08acff?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'bedding-bath': [
        {
            'name': '1000 Thread Count Egyptian Cotton Sheet Set',
            'description': 'Silky-smooth king size sheet set including fitted sheet, flat sheet, and 2 pillowcases.',
            'price': Decimal('129.99'),
            'image_url': 'https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Plush Turkish Cotton Bath Towels (Pack of 4)',
            'description': 'Ultra-absorbent 700 GSM 100% combed Turkish cotton bath towels for hotel luxury at home.',
            'price': Decimal('54.99'),
            'image_url': 'https://images.unsplash.com/photo-1616627547584-bf28cee262db?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'lighting-fixtures': [
        {
            'name': 'Nordic Arc Floor Lamp with Marble Base',
            'description': 'Contemporary overhead arc lamp with brass finish, fabric shade, and heavy marble base.',
            'price': Decimal('149.00'),
            'image_url': 'https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Smart LED Dimmable Desk Lamp with Wireless Charger',
            'description': 'Eye-care LED desk lamp featuring 5 color modes, touch dimmer slider, and wireless phone charging pad.',
            'price': Decimal('42.99'),
            'image_url': 'https://images.unsplash.com/photo-1534349762230-e0cadf78f5da?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'skincare': [
        {
            'name': 'HydraGlow Vitamin C Serum 30ml',
            'description': 'Antioxidant-rich facial serum formulated with 15% pure Vitamin C, Hyaluronic Acid, and Ferulic Acid.',
            'price': Decimal('38.00'),
            'image_url': 'https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Gentle Hydrating Facial Cleanser 200ml',
            'description': 'pH-balanced cream cleanser enriched with ceramides and niacinamide to restore the skin barrier.',
            'price': Decimal('24.50'),
            'image_url': 'https://images.unsplash.com/photo-1556228720-195a672e8a03?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'haircare': [
        {
            'name': 'Nourishing Argan Oil Repair Hair Mask',
            'description': 'Deep conditioning treatment mask infused with cold-pressed Moroccan Argan Oil and Keratin.',
            'price': Decimal('29.99'),
            'image_url': 'https://images.unsplash.com/photo-1535585209827-a15fcdbc4c2d?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Ionic High-Speed Hair Dryer with Concentrator',
            'description': 'Professional 1800W negative ion blow dryer for fast drying without heat damage.',
            'price': Decimal('89.99'),
            'image_url': 'https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'makeup-cosmetics': [
        {
            'name': 'Velvet Matte Long-Wear Lipstick',
            'description': 'Highly-pigmented creamy matte lipstick delivering 12-hour comfortable wear in classic red.',
            'price': Decimal('22.00'),
            'image_url': 'https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Nude Eyeshadow Palette (12 Shades)',
            'description': 'Versatile eyeshadow palette with ultra-blendable matte, shimmer, and metallic neutral tones.',
            'price': Decimal('36.50'),
            'image_url': 'https://images.unsplash.com/photo-1512496015851-a90fb38ba796?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'fragrances-perfumes': [
        {
            'name': 'Mystic Oud Eau de Parfum 100ml',
            'description': 'Luxurious unisex fragrance blending rich agarwood, amber, rose, and warm sandalwood notes.',
            'price': Decimal('115.00'),
            'image_url': 'https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Citrus Breeze Fresh Cologne 50ml',
            'description': 'Revitalizing fresh scent with notes of Italian bergamot, grapefruit, and coastal cedarwood.',
            'price': Decimal('65.00'),
            'image_url': 'https://images.unsplash.com/photo-1541643600914-78b084683601?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'personal-hygiene': [
        {
            'name': 'Sonic Electric Toothbrush with 4 Brush Heads',
            'description': 'Rechargeable sonic toothbrush generating 40,000 vibrations/min with 5 cleaning modes.',
            'price': Decimal('49.99'),
            'image_url': 'https://images.unsplash.com/photo-1559591937-e68fb3305e40?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Natural Botanical Body Wash 500ml',
            'description': 'Sulfate-free moisturizing body wash with organic aloe vera, lavender, and eucalyptus extracts.',
            'price': Decimal('18.99'),
            'image_url': 'https://images.unsplash.com/photo-1608248597461-00d96637118b?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'exercise-fitness-equipment': [
        {
            'name': 'Adjustable Dumbbell Set (5-52.5 lbs)',
            'description': 'Compact space-saving adjustable dumbbell system replaces 15 sets of weights.',
            'price': Decimal('329.00'),
            'image_url': 'https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Non-Slip TPE Yoga Mat 6mm',
            'description': 'Eco-friendly high-density yoga mat with body alignment markings and carrying strap.',
            'price': Decimal('35.99'),
            'image_url': 'https://images.unsplash.com/photo-1601925260368-ae2f83cf8b7f?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'outdoor-recreation-camping': [
        {
            'name': 'Waterproof 4-Person Camping Tent',
            'description': 'Easy setup dome tent with rainfly, mesh windows, and windproof aluminum poles.',
            'price': Decimal('149.99'),
            'image_url': 'https://images.unsplash.com/photo-1504280390367-361c6d9f38f4?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Insulated Stainless Steel Water Bottle 32oz',
            'description': 'Double-wall vacuum insulated canteen keeps drinks cold for 24h or hot for 12h.',
            'price': Decimal('27.99'),
            'image_url': 'https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'athletic-apparel': [
        {
            'name': 'Dry-Fit Performance Training Hoodie',
            'description': 'Moisture-wicking athletic hoodie with thumbholes and zippered kangaroo pocket.',
            'price': Decimal('59.99'),
            'image_url': 'https://images.unsplash.com/photo-1556905055-8f358a7a47b2?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'High-Waisted Seamless Workout Leggings',
            'description': 'Squat-proof compression yoga leggings with side pockets and tummy control waistband.',
            'price': Decimal('48.00'),
            'image_url': 'https://images.unsplash.com/photo-1506629082955-511b1aa562c8?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'cycling-scooters': [
        {
            'name': 'Foldable Electric Scooter 350W',
            'description': 'Commuter e-scooter with 19 mph top speed, 18-mile range, and pneumatic 8.5-inch tires.',
            'price': Decimal('429.00'),
            'image_url': 'https://images.unsplash.com/photo-1558981806-ec527fa84c39?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Aerodynamic Road Bike Helmet',
            'description': 'Lightweight bicycle helmet with MIPS safety protection system and dial adjustment.',
            'price': Decimal('79.99'),
            'image_url': 'https://images.unsplash.com/photo-1557804506-669a67965ba0?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'action-figures-toys': [
        {
            'name': 'Galactic Hero Articulated Action Figure 12-inch',
            'description': 'Collectible sci-fi superhero figure with sound effects, LED visor, and interchangeable accessories.',
            'price': Decimal('34.99'),
            'image_url': 'https://images.unsplash.com/photo-1608889825205-eebdb9fc5806?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Remote Control High-Speed Off-Road Stunt Car',
            'description': '4WD RC monster truck with 2.4GHz remote control, rechargeable battery, and 360 flip capabilities.',
            'price': Decimal('49.50'),
            'image_url': 'https://images.unsplash.com/photo-1594787318286-3d835c1d207f?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'board-games-puzzles': [
        {
            'name': 'Kingdoms Strategy Board Game Edition',
            'description': 'Engaging tactical board game for 2-4 players with detailed miniature figures and custom dice.',
            'price': Decimal('54.99'),
            'image_url': 'https://images.unsplash.com/photo-1610890716171-6b1bb98ffd09?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': '1000-Piece Landscape Jigsaw Puzzle',
            'description': 'Premium cardboard jigsaw puzzle featuring a vibrant alpine lake mountain photography print.',
            'price': Decimal('19.99'),
            'image_url': 'https://images.unsplash.com/photo-1585336261026-8f5786372969?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'crafts-hobbies': [
        {
            'name': 'Complete Acrylic Painting Supplies Kit',
            'description': 'Art set includes 24 acrylic paint tubes, tabletop wooden easel, stretched canvases, and 12 brushes.',
            'price': Decimal('45.99'),
            'image_url': 'https://images.unsplash.com/photo-1513364776144-60967b0f800f?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Beginner Pottery & Clay Crafting Kit',
            'description': 'Air-dry clay sculpting starter set with shaping tools, paints, varnish, and step-by-step guidebook.',
            'price': Decimal('38.50'),
            'image_url': 'https://images.unsplash.com/photo-1565193566173-7a0ee3dbe261?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'car-accessories': [
        {
            'name': 'Dash Cam Front and Rear 4K Ultra HD',
            'description': 'Dual car camera with night vision, built-in GPS, Wi-Fi connectivity, and G-sensor loop recording.',
            'price': Decimal('119.99'),
            'image_url': 'https://images.unsplash.com/photo-1549399542-7e3f8b79c341?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Wireless Car Charger Mount & Phone Holder',
            'description': 'Auto-clamping Qi 15W fast wireless car charging mount compatible with all smart devices.',
            'price': Decimal('34.99'),
            'image_url': 'https://images.unsplash.com/photo-1511919884226-fd3cad34687c?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'auto-parts': [
        {
            'name': 'High-Performance Ceramic Brake Pads Set',
            'description': 'Low-dust, quiet ceramic brake pads designed for maximum stopping power and heat resistance.',
            'price': Decimal('64.99'),
            'image_url': 'https://images.unsplash.com/photo-1486006920555-c77dce18193b?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Universal Heavy-Duty Car Battery Charger 12V/24V',
            'description': 'Automatic smart battery maintainer and trickle charger with pulse repair technology.',
            'price': Decimal('55.00'),
            'image_url': 'https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'hand-power-tools': [
        {
            'name': '20V Cordless Brushless Drill Driver Combo Kit',
            'description': 'Includes 20V drill, 2 lithium-ion batteries, fast charger, 30 screwdriver bits, and carry bag.',
            'price': Decimal('139.99'),
            'image_url': 'https://images.unsplash.com/photo-1504148455328-c376907d081c?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Mechanics Tool Set 108-Piece Socket Wrench Kit',
            'description': 'Chrome vanadium steel socket set with 72-tooth ratchets in a sturdy blow-molded case.',
            'price': Decimal('89.00'),
            'image_url': 'https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'books-literature': [
        {
            'name': 'The Midnight Library - Hardcover Novel',
            'description': 'Bestselling fiction novel exploring parallel lives, second choices, and the power of decisions.',
            'price': Decimal('24.99'),
            'image_url': 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Atomic Habits: An Easy & Proven Way to Build Good Habits',
            'description': 'Transformative personal development handbook by James Clear offering actionable strategies.',
            'price': Decimal('21.00'),
            'image_url': 'https://images.unsplash.com/photo-1512820790803-83ca734da794?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'office-school-supplies': [
        {
            'name': 'Fountain Pen & Journal Gift Box',
            'description': 'Handcrafted leather-bound notebook with 100gsm archival paper and fine nib metal fountain pen.',
            'price': Decimal('39.99'),
            'image_url': 'https://images.unsplash.com/photo-1583485088034-697b5bc54ccd?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Ergonomic Desk Organizer Set',
            'description': '5-piece mesh steel office desk set including paper tray, pen holder, and sticky note dispenser.',
            'price': Decimal('28.50'),
            'image_url': 'https://images.unsplash.com/photo-1507842217343-583bb7270b66?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'music-video': [
        {
            'name': 'Vintage Bluetooth Turntable Vinyl Record Player',
            'description': '3-speed suitcase turntable with built-in stereo speakers and wireless Bluetooth audio streaming.',
            'price': Decimal('79.99'),
            'image_url': 'https://images.unsplash.com/photo-1539375665275-f9de415ef9ac?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Acoustic Guitar Starter Pack',
            'description': 'Full-size 41-inch dreadnought wooden acoustic guitar with gig bag, tuner, strap, and picks.',
            'price': Decimal('149.00'),
            'image_url': 'https://images.unsplash.com/photo-1510915361894-db8b60106cb1?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'beverages-coffee': [
        {
            'name': 'Artisanal Single-Origin Arabica Whole Bean Coffee 1kg',
            'description': 'Medium-dark roast specialty Ethiopian Yirgacheffe coffee beans with floral and chocolate notes.',
            'price': Decimal('26.99'),
            'image_url': 'https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Organic Ceremonial Grade Matcha Green Tea Powder 100g',
            'description': '100% pure shade-grown Japanese green tea leaves ground into fine vibrant green powder.',
            'price': Decimal('29.50'),
            'image_url': 'https://images.unsplash.com/photo-1536256263959-770b48d82b0a?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'snacks-confectionery': [
        {
            'name': 'Gourmet Belgian Dark Chocolate Gift Box 24-Piece',
            'description': 'Handcrafted praline chocolates filled with ganache, hazelnut truffles, and salted caramel.',
            'price': Decimal('32.00'),
            'image_url': 'https://images.unsplash.com/photo-1549007994-cb92caebd54b?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Roasted Honey Glazed Mixed Nuts 500g',
            'description': 'Crunchy blend of almonds, cashews, pecans, and walnuts lightly seasoned with sea salt and honey.',
            'price': Decimal('18.50'),
            'image_url': 'https://images.unsplash.com/photo-1536591375315-1b83689e377a?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'pantry-staples': [
        {
            'name': 'Extra Virgin Organic Cold-Pressed Olive Oil 1L',
            'description': 'First cold-pressed single estate Spanish extra virgin olive oil bottled in dark glass.',
            'price': Decimal('22.99'),
            'image_url': 'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Himalayan Pink Rock Salt Grinder set 250g',
            'description': 'Pure unrefined pink salt crystals harvested from ancient seabed deposits with ceramic grinder.',
            'price': Decimal('14.99'),
            'image_url': 'https://images.unsplash.com/photo-1518110165401-447a16f2c310?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'software-licenses': [
        {
            'name': 'Cloud Security Suite Pro 1-Year License',
            'description': 'All-in-one antivirus, firewall, VPN, and identity protection software for up to 5 devices.',
            'price': Decimal('59.99'),
            'image_url': 'https://images.unsplash.com/photo-1563986768609-322da13575f3?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Creative Studio Master Suite Lifetime Pass',
            'description': 'Comprehensive digital photo editing, vector design, and video editor desktop license key.',
            'price': Decimal('199.00'),
            'image_url': 'https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=800&auto=format&fit=crop&q=80',
        }
    ],
    'ebooks-digital-courses': [
        {
            'name': 'Full-Stack Web Development Bootcamp Course E-Book',
            'description': 'Complete 500-page modern guide covering React, Node.js, Python Django, PostgreSQL, and DevOps.',
            'price': Decimal('29.99'),
            'image_url': 'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=800&auto=format&fit=crop&q=80',
        },
        {
            'name': 'Mastering Algorithmic Stock Trading eBook',
            'description': 'Step-by-step digital manual on quantitative finance strategies, backtesting, and automated bots.',
            'price': Decimal('34.50'),
            'image_url': 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&auto=format&fit=crop&q=80',
        }
    ]
}

DEFAULT_FALLBACK_PRODUCTS = [
    {
        'name': 'Premium Quality Product',
        'description': 'High performance durable item crafted with top tier materials and modern aesthetics.',
        'price': Decimal('49.99'),
        'image_url': 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&auto=format&fit=crop&q=80',
    },
    {
        'name': 'Deluxe Edition Product',
        'description': 'Versatile high reliability product featuring sleek design and long term utility.',
        'price': Decimal('89.99'),
        'image_url': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&auto=format&fit=crop&q=80',
    }
]


class Command(BaseCommand):
    help = 'Seeds at least 2 products with images for every subcategory for tenant kadosh.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"Starting Product Seeding for Tenant ID: {KADOSH_TENANT_ID}..."))

        subcategories = Category.objects.filter(parent__isnull=False)
        self.stdout.write(f"Found {subcategories.count()} subcategories.")

        total_created = 0

        for subcat in subcategories:
            existing_count = Product.objects.filter(subcategory=subcat, tenant_id=KADOSH_TENANT_ID).count()
            needed = max(0, 2 - existing_count)

            if needed == 0:
                self.stdout.write(f"Subcategory '{subcat.name}' already has {existing_count} products. Skipping.")
                continue

            products_data = SUBCATEGORY_PRODUCTS.get(subcat.slug, DEFAULT_FALLBACK_PRODUCTS)

            for i in range(needed):
                prod_spec = products_data[i % len(products_data)]
                sku_base = subcat.slug.replace('-', '').upper()[:8]
                sku = f"KAD-{sku_base}-{uuid.uuid4().hex[:6].upper()}"

                product = Product.objects.create(
                    tenant_id=KADOSH_TENANT_ID,
                    name=prod_spec['name'],
                    description=prod_spec['description'],
                    sku=sku,
                    category=subcat.parent,
                    subcategory=subcat
                )

                # Price
                ProductPrice.objects.create(
                    product=product,
                    tenant_id=KADOSH_TENANT_ID,
                    base_price=prod_spec['price'],
                    cost_price=prod_spec['price'] * Decimal('0.6'),
                    currency='USD'
                )

                # Image
                ProductImage.objects.create(
                    product=product,
                    tenant_id=KADOSH_TENANT_ID,
                    image_url=prod_spec['image_url'],
                    alt_text=prod_spec['name'],
                    is_primary=True,
                    display_order=1
                )

                # Variant with Stock
                ProductVariant.objects.create(
                    product=product,
                    tenant_id=KADOSH_TENANT_ID,
                    sku=f"{product.sku}-VAR1",
                    price=prod_spec['price'],
                    stock=50,
                    is_active=True
                )

                total_created += 1
                self.stdout.write(self.style.SUCCESS(
                    f"Created product '{product.name}' (SKU: {product.sku}) in '{subcat.parent.name} -> {subcat.name}'"
                ))

        self.stdout.write(self.style.SUCCESS(
            f"Product seeding completed! Created {total_created} new products across all subcategories."
        ))
