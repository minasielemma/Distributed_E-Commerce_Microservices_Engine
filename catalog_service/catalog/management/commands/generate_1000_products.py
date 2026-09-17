import uuid
import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from catalog.models import (
    Category,
    Product,
    ProductPrice,
    ProductVariant,
    ProductAttribute,
    ProductAttributeValue,
    ProductImage
)

# Kadosh Shop default tenant ID
DEFAULT_TENANT_ID = uuid.UUID('21e17510-301a-4f06-88ac-5a011c88b96d')

CATEGORIES_TAXONOMY = {
    "Electronics & Gadgets": ["Smartphones", "Laptops", "Tablets", "Headphones", "Smartwatches", "Cameras", "Speakers", "Monitors", "Drones", "Gaming Consoles", "Power Banks", "Chargers", "Memory Cards", "Projectors", "VR Headsets"],
    "Fashion & Apparel": ["Men's Shirts", "Men's Pants", "Women's Dresses", "Women's Tops", "Jackets & Coats", "Sweaters & Hoodies", "Activewear", "Swimwear", "Underwear & Sleepwear", "Suits & Blazers", "Kids' Apparel", "Baby Clothing", "Socks & Hosiery", "Belts & Ties", "Hats & Caps"],
    "Footwear": ["Running Shoes", "Sneakers", "Boots", "Dress Shoes", "Sandals & Flip Flops", "Loafers", "Heels & Pumps", "Flats", "Slippers", "Athletic Cleats", "Hiking Boots", "Work Boots", "Canvas Shoes", "Platform Shoes", "Water Shoes"],
    "Jewelry & Accessories": ["Necklaces", "Rings", "Earrings", "Bracelets", "Watches", "Sunglasses", "Wallets", "Handbags", "Backpacks", "Travel Luggage", "Scarves & Wraps", "Hair Accessories", "Brooches", "Cufflinks", "Keychains"],
    "Home & Living": ["Sofas & Couches", "Beds & Mattresses", "Dining Tables", "Office Chairs", "Storage Cabinets", "Coffee Tables", "Bookshelves", "TV Stands", "Wardrobes", "Recliners", "Bar Stools", "Ottomans", "Desks", "Dressers", "Futons"],
    "Kitchen & Dining": ["Cookware Sets", "Bakeware", "Cutlery & Knives", "Dinnerware", "Drinkware", "Small Kitchen Appliances", "Coffee Makers", "Blenders & Juicers", "Air Fryers", "Microwaves", "Toasters", "Food Storage", "Kitchen Utensils", "Table Linens", "Barware"],
    "Bedding & Bath": ["Bed Sheets", "Comforters & Duvets", "Pillows", "Blankets & Throws", "Mattress Toppers", "Towels & Washcloths", "Bath Mats", "Shower Curtains", "Bathrobes", "Bed Skirts", "Duvet Covers", "Body Pillows", "Hand Towels", "Bath Caddies", "Scale & Bathroom Decor"],
    "Home Decor & Lighting": ["Wall Art & Canvas", "Mirrors", "Vases & Bowls", "Candles & Holders", "Clocks", "Indoor Rugs", "Curtains & Drapes", "Floor Lamps", "Table Lamps", "Pendant Lights", "Ceiling Fans", "Chandelier Lights", "Decorative Pillows", "Artificial Plants", "Picture Frames"],
    "Beauty & Skincare": ["Facial Cleansers", "Moisturizers", "Serums & Oils", "Face Masks", "Sunscreen", "Eye Creams", "Toners", "Exfoliators", "Lip Balms", "Anti-Aging Treatments", "Acne Care", "Makeup Removers", "Facial Tools", "Sheet Masks", "Night Creams"],
    "Makeup & Cosmetics": ["Foundations", "Lipsticks & Glosses", "Mascaras", "Eyeliners", "Eye Shadow Palettes", "Concealers", "Blushes & Highlighters", "Setting Powders", "Makeup Brushes", "Primer", "Setting Sprays", "Bronzers", "Eyebrow Pencils", "Nail Polish", "Cosmetic Bags"],
    "Hair Care & Styling": ["Shampoos", "Conditioners", "Hair Masks & Oils", "Hair Dryers", "Flat Irons & Straighteners", "Curling Irons", "Hair Styling Gels", "Hair Sprays", "Hair Color & Dye", "Scalp Treatments", "Hair Brushes & Combs", "Hair Extension Tools", "Beard Care", "Dry Shampoo", "Hair Loss Treatments"],
    "Personal Care & Hygiene": ["Body Wash & Soap", "Deodorants", "Oral Care & Toothbrushes", "Shaving & Trimming", "Feminine Hygiene", "Hand Sanitizers", "Bath Bombs", "Foot Care", "Cotton Swabs & Pads", "First Aid Essentials", "Ear Care", "Incontinence Products", "Sun Care", "Tissues & Wipes", "Massage Oil"],
    "Fragrances": ["Eau de Parfum", "Eau de Toilette", "Cologne", "Body Sprays", "Perfume Oils", "Unisex Scents", "Solid Perfumes", "Miniature Gift Sets", "Roll-on Perfumes", "Niche Fragrances", "Organic Fragrances", "Scented Lotions", "Aftershave Balms", "Home Diffusers", "Aromatherapy Oils"],
    "Sports & Fitness": ["Treadmills & Bikes", "Dumbbells & Weights", "Yoga Mats", "Resistance Bands", "Jump Ropes", "Pull-up Bars", "Kettlebells", "Gym Bags", "Foam Rollers", "Heart Rate Monitors", "Boxing Gloves", "Fitness Trackers", "Bench Presses", "Weight Vests", "Agility Ladders"],
    "Outdoor & Camping": ["Tents & Shelters", "Sleeping Bags", "Camping Stoves", "Backpacking Packs", "Hiking Boots", "Lanterns & Flashlights", "Hydration Packs", "Camp Chairs", "Coolers & Ice Chests", "Trekking Poles", "Outdoor Navigation & GPS", "Insect Repellent", "Hammocks", "Camp Cookware", "First Aid Kits"],
    "Cycling & Scooters": ["Road Bikes", "Mountain Bikes", "Electric Bikes", "Electric Scooters", "Bike Helmets", "Bike Locks", "Cycling Apparel", "Bike Lights", "Bike Pumps", "Bike Bags & Panniers", "Pedals & Cleats", "Bike Tools & Repair", "Water Bottle Cages", "Child Bike Seats", "Scooter Accessories"],
    "Water Sports": ["Kayaks & Canoes", "Paddleboards (SUP)", "Life Jackets & Vests", "Snorkeling & Scuba Gear", "Wetsuits & Rashguards", "Swim Goggles", "Swim Caps", "Dry Bags", "Towable Tubes", "Surfboards", "Wakeboards", "Water Skis", "Pool Floats", "Fins & Flippers", "Water Shoes"],
    "Team Sports": ["Soccer Balls & Gear", "Basketballs & Hoops", "Baseball Gloves & Bats", "Football Gear", "Volleyballs & Nets", "Tennis Rackets & Balls", "Golf Clubs & Bags", "Hockey Sticks & Skates", "Rugby Balls", "Lacrosse Gear", "Cricket Bats & Gear", "Table Tennis Rackets", "Badminton Sets", "Bowling Balls", "Squash Rackets"],
    "Toys & Action Figures": ["Action Figures", "Dollhouses & Dolls", "Building Sets & Bricks", "Remote Control Vehicles", "Plush & Stuffed Animals", "Educational Toys", "Die-cast Cars", "Pretend Play Sets", "Water Toys", "Ride-on Toys", "Robotic Toys", "Playsets", "Toy Weapons & Blasters", "Puzzles for Kids", "Finger Puppets"],
    "Board Games & Puzzles": ["Strategy Board Games", "Family Board Games", "Card Games", "Jigsaw Puzzles 1000-piece", "Chess & Checkers", "Dice Games", "Trivia Games", "Party Games", "Role-Playing Games (RPG)", "Word Games", "Tile Games", "Domino Sets", "Brain Teaser Puzzles", "3D Puzzles", "Collectible Card Games"],
    "Crafts & Hobbies": ["Painting & Drawing Supplies", "Knitting & Crochet", "Sewing & Fabrics", "Model Building Kits", "Clay & Sculpting", "Jewelry Making Kits", "Scrapbooking & Paper", "Candle Making Supplies", "Resin Craft Kits", "Embroidery Sets", "Calligraphy Pens", "Stamp & Ink Sets", "Leathercraft Tools", "Beading Supplies", "Origami Paper"],
    "Automotive Accessories": ["Car Seat Covers", "Floor Mats", "Car Phone Mounts", "Car Dash Cams", "Car Cleaning & Detailing", "LED Headlights", "Car Audio & Speakers", "GPS Navigators", "Car Cover Protectors", "Emergency Jumper Starters", "Tire Pressure Gauges", "Roof Racks & Cargo", "Car Air Fresheners", "Trunk Organizers", "Windshield Wipers"],
    "Auto Parts & Tools": ["Brake Pads & Rotors", "Oil Filters & Engine Oils", "Spark Plugs", "Car Batteries", "Air Filters", "Alternators & Starters", "Diagnostic OBD2 Scanners", "Mechanics Tool Sets", "Hydraulic Jacks", "Tire Repair Kits", "Engine Fluids", "Fuel Pumps", "Radiators & Cooling", "Exhaust Parts", "Suspension Springs"],
    "Hand & Power Tools": ["Cordless Drills", "Circular Saws", "Hammer Drills", "Tool Boxes & Chests", "Wrench & Socket Sets", "Screwdriver Sets", "Pliers & Cutters", "Measuring Tapes & Levels", "Angle Grinders", "Impact Drivers", "Air Compressors", "Workbenches", "Safety Goggles & Gloves", "Soldering Irons", "Heat Guns"],
    "Lawn & Garden": ["Lawn Mowers", "String Trimmers", "Leaf Blowers", "Garden Hoses & Nozzles", "Planters & Pots", "Garden Hand Tools", "Fertilizers & Soil", "Patio Furniture", "Outdoor Grills & BBQ", "Fire Pits", "Shade Sails & Umbrellas", "Sprinklers & Irrigation", "Compost Bins", "Greenhouses", "Pest Control Outdoor"],
    "Books & Literature": ["Fiction Novels", "Non-Fiction & Biographies", "Self-Help & Personal Growth", "Business & Finance Books", "Cookbooks & Culinary Arts", "Science Fiction & Fantasy", "Mystery & Thrillers", "History Books", "Children's Picture Books", "Young Adult Fiction", "Comics & Graphic Novels", "Textbooks & Education", "Art & Photography Books", "Poetry Collections", "Travel Guides"],
    "Office & School Supplies": ["Notebooks & Journals", "Pens & Pencils", "Staplers & Hole Punches", "Desk Organizers", "Calculators", "File Folders & Binders", "Printer Paper", "Sticky Notes & Flags", "Whiteboards & Markers", "Scissors & Paper Cutters", "Envelopes & Shipping", "Highlighters", "Tape & Adhesives", "Clipboards", "Correction Tape"],
    "Music & Audio Equipment": ["Acoustic Guitars", "Electric Guitars", "Digital Pianos & Keyboards", "Microphones & Stands", "Audio Interfaces", "Studio Monitors", "Drum Kits & Percussion", "DJ Controllers", "Violins & String Instruments", "Ukuleles", "Brass & Woodwind", "Headphone Amplifiers", "MIDI Controllers", "Effects Pedals", "Sheet Music Stands"],
    "Groceries & Pantry": ["Ground & Whole Bean Coffee", "Tea Bags & Loose Leaf", "Pasta & Noodles", "Canned Beans & Vegetables", "Cooking Oils & Vinegars", "Spices & Seasonings", "Breakfast Cereals & Oats", "Snack Nuts & Dried Fruit", "Chips & Pretzels", "Chocolates & Candies", "Baking Mixes & Flour", "Sauces & Condiments", "Jams & Spreads", "Protein Bars", "Organic Juices"],
    "Pet Supplies": ["Dog Food & Kibble", "Dog Toys & Chews", "Cat Food & Treats", "Cat Litter & Boxes", "Dog Beds & Crates", "Pet Leashes & Collars", "Fish Tanks & Aquariums", "Bird Cages & Seed", "Small Animal Cages", "Pet Grooming Brushes", "Flea & Tick Treatments", "Pet Carriers & Strollers", "Aquarium Filters", "Reptile Heating & Lighting", "Pet Flea Shampoos"],
    "Baby & Toddler": ["Baby Strollers", "Car Seats", "Baby Cribs & Bassinets", "Diapers & Wipes", "Baby Formula & Food", "Feeding Bottles", "Baby Carriers & Wraps", "High Chairs", "Pacifiers & Teethers", "Baby Monitors", "Baby Bath Tubs", "Safety Gates & Locks", "Nursery Decor", "Swaddles & Blankets", "Diaper Bags"],
    "Smart Home & Automation": ["Smart Doorbell Cameras", "Smart Thermostats", "Smart Door Locks", "Smart Security Systems", "Smart Light Bulbs", "Smart Plugs & Outlets", "Smart Robot Vacuums", "Smart Speakers & Hubs", "Smart Window Blinds", "Smart Smoke Detectors", "Smart Water Leak Sensors", "Smart Garage Openers", "Smart Switches", "Smart Energy Monitors", "Smart Lawn Sprinklers"],
    "Cameras & Optics": ["DSLR Cameras", "Mirrorless Cameras", "Action Cameras", "Camera Lenses", "Tripods & Monopods", "Camera Bags & Cases", "Binoculars & Telescopes", "Camera Flash & Lighting", "Gimbals & Stabilizers", "Filters & Hoods", "Memory Card Readers", "Drone Cameras", "Microphones for Video", "Security Cameras", "Underwater Camera Cases"],
    "Computers & Accessories": ["Gaming PCs", "Desktop Computers", "Computer Monitors", "Keyboards & Mice", "External Hard Drives", "Solid State Drives (SSD)", "PC Power Supplies", "Computer Graphics Cards (GPU)", "RAM Memory Modules", "PC Motherboards", "CPU Coolers", "Docking Stations", "Webcams & Ring Lights", "Networking Routers & Mesh", "PC Computer Cases"],
    "Cell Phones & Accessories": ["Unlocked Smartphones", "Phone Cases & Covers", "Screen Protectors", "Wireless Charging Pads", "Car Phone Chargers", "Phone Grip Holders", "Selfie Sticks & Tripods", "Lightning & USB-C Cables", "Bluetooth Earpieces", "Portable Battery Packs", "Phone Lanyards", "SIM Card Accessories", "Phone Repair Kits", "Mobile Game Controllers", "Stylus Pens"],
    "TV & Home Theater": ["4K Smart TVs", "OLED & QLED TVs", "Soundbars & Subwoofers", "Home Theater Receivers", "Streaming Media Players", "Projector Screens", "TV Wall Mounts", "Universal Remote Controls", "HDMI Cables & Adapters", "Blu-ray & DVD Players", "Wireless Audio Transmitters", "Surround Sound Speakers", "TV Antennas", "AV Furniture Stands", "Cable Management Kits"],
    "Video Games": ["PlayStation Consoles", "PlayStation Games", "Xbox Consoles", "Xbox Games", "Nintendo Switch Consoles", "Nintendo Games", "Gaming Headsets", "Wireless Controllers", "Gaming Chairs", "VR Controllers & Accessories", "Retro Arcade Cabinets", "Gaming Steering Wheels", "Controller Charging Docks", "Gaming Desk Pads", "Video Game Gift Cards"],
    "Stationery & Paper Goods": ["Luxury Fountain Pens", "Calligraphy Markers", "Custom Stamps", "Greeting Cards", "Wrapping Paper & Ribbons", "Planner Dividers & Stickers", "Wax Seal Kits", "Handmade Paper", "Drafting Pencils", "Sketchbooks", "Desk Blotters", "Bookmark Clips", "Envelope Seals", "Correction Fluids", "Architectural Scales"],
    "Health & Wellness": ["Massage Guns", "Heating Pads", "Blood Pressure Monitors", "Digital Thermometers", "Pulse Oximeters", "Posture Correctors", "CPAP Accessories", "Essential Oil Diffusers", "Aromatherapy Sets", "Weight Scales & BMI", "Light Therapy Lamps", "Eye Massagers", "Humidifiers", "Air Purifiers", "Sound Noise Machines"],
    "Vitamins & Supplements": ["Multivitamins", "Protein Powders", "Omega-3 Fish Oil", "Probiotics", "Vitamin C & Zinc", "Collagen Peptides", "Creatine Monohydrate", "Pre-Workout Supplements", "Vitamin D3", "Magnesium Supplements", "Melatonin Sleep Aids", "BCAA Amino Acids", "Herbal Extracts", "Keto Supplements", "Fiber Supplements"],
    "Industrial & Scientific": ["3D Printers & Filaments", "Lab Microscopes", "Digital Calipers", "Thermal Imagers", "Safety Helmets & Vests", "Lab Flasks & Beakers", "Scale Balances", "Industrial Tape", "Protective Eyewear", "Soldering Stations", "Oscilloscopes", "Multimeters", "Cleanroom Wipes", "Chemical Storage Containers", "Barcode Scanners"],
    "Plumbing & Fixtures": ["Bathroom Faucets", "Kitchen Sink Faucets", "Shower Heads & Systems", "Toilets & Bidets", "Kitchen Sinks", "Sump Pumps", "Water Heaters", "Pipe Fittings & Valves", "Drain Cleaning Cables", "Plumbing Snakes", "Water Filtration Systems", "Garbage Disposals", "Pipe Insulation", "Hose Bibbs", "Plumbing Sealants"],
    "Electrical & Hardware": ["Circuit Breakers", "Electrical Wire & Cables", "Wall Switches & Dimmers", "Electrical Outlets", "Junction Boxes", "Conduit Pipes", "Extension Cords", "Voltage Testers", "Wire Strippers", "Cable Ties & Clips", "Solar Panels", "Power Inverters", "Generator Systems", "Fuse Blocks", "Electrical Tape"],
    "Building Supplies": ["Drywall Anchors", "Screws & Bolts", "Nails & Rivets", "Wall Insulation", "Roofing Shingles", "Caulking & Sealants", "Plywood Sheets", "Cement & Concrete Mix", "Tile Grout", "Sandpaper & Abrasives", "Adhesive Tapes", "Safety Masks", "Ladders & Stepladders", "Tarps & Covers", "Scaffolding Equipment"],
    "Paint & Wall Treatments": ["Interior Wall Paint", "Exterior House Paint", "Spray Paint Cans", "Paint Rollers & Trays", "Paint Brushes", "Painter's Tape", "Wallpaper Rolls", "Primer Paint", "Wood Stain & Varnish", "Drywall Spackle", "Paint Sprayers", "Drop Cloths", "Paint Scrapers", "Color Swatch Cards", "Epoxy Floor Kits"],
    "Storage & Organization": ["Plastic Storage Bins", "Closet Organizers", "Shoe Racks", "Garment Racks", "Under-Bed Storage", "Pantry Bins", "Garage Shelving Units", "Drawer Dividers", "Hanging Closet Organizers", "Storage Trunks", "Vacuum Storage Bags", "Pegboards & Hooks", "Cube Storage Shelves", "Moving Boxes", "Label Makers"],
    "Party & Event Supplies": ["Balloons & Helium", "Party Streamers", "Disposable Tableware", "Cake Toppers", "Party Favors", "Photo Booth Props", "Banners & Signs", "Confetti Poppers", "Table Centerpieces", "Event Lighting", "Invitation Cards", "Goodie Bags", "Pinatas", "Catering Trays", "Table Skirts"],
    "Musical Instruments (Traditional)": ["Violins & Fiddles", "Cellos & Double Bass", "Trumpets & Trombones", "Saxophones & Clarinets", "Flutes & Piccolos", "Accordions", "Harmonicas", "Xylophones & Marimbas", "Harps", "Mandolins & Banjos", "Bagpipes", "Tablas & Hand Drums", "French Horns", "Oboes & Bassoons", "Tambourines"],
    "Collectibles & Memorabilia": ["Coin Sets & Bullion", "Stamp Collections", "Autographed Sports Memorabilia", "Comic Book Key Issues", "Vintage Postcards", "Die-cast Model Aircraft", "Historical Relics", "Movie Props & Replicas", "Trading Card Booster Boxes", "Antique Pocket Watches", "Vintage Vinyl Records", "Military Pin Badges", "First Edition Books", "Fine China Teacups", "Signed Guitars"],
    "Travel & Luggage": ["Hard-shell Suitcases", "Soft-side Luggage", "Carry-on Backpacks", "Duffle Bags", "Garment Travel Bags", "Packing Cubes", "Travel Pillows", "TSA Approved Locks", "Luggage Tags", "Passport Holders", "Toiletry Bags", "Travel Adapter Plugs", "Money Belts", "Luggage Scales", "Travel Compress Bags"],
    "Safety & Security": ["Home Fire Extinguishers", "Smoke & CO Detectors", "Personal Pepper Sprays", "Safes & Lock Boxes", "First Aid Trauma Kits", "Emergency Food Rations", "Solar Hand-Crank Radios", "Security Door Barricades", "Window Security Film", "Escape Ladders", "Reflective Vests", "High-Decibel Alarms", "Work Gloves", "Hazard Cones", "Safety Whistles"],
    "Novelty & Gifts": ["Customized Photo Mugs", "Funny T-Shirts", "Gag Gifts", "Personalized Keychains", "Engraved Pens", "Custom Doormats", "Novelty Socks", "Custom Canvas Prints", "Gift Baskets", "Funny Desk Signs", "Personalized Cutting Boards", "Custom Enamel Pins", "Unique Bobbleheads", "Light-up Tumblers", "Puzzle Box Gifts"]
}

IMAGE_POOL = [
    'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9',
    'https://images.unsplash.com/photo-1598327105666-5b89351aff97',
    'https://images.unsplash.com/photo-1517336714731-489689fd1ca8',
    'https://images.unsplash.com/photo-1603302576837-37561b2e2302',
    'https://images.unsplash.com/photo-1505740420928-5e560c06d30e',
    'https://images.unsplash.com/photo-1590658268037-6bf12165a8df',
    'https://images.unsplash.com/photo-1516035069371-29a1b244cc32',
    'https://images.unsplash.com/photo-1523275335684-37898b6baf30',
    'https://images.unsplash.com/photo-1583863788434-e58a36330cf0',
    'https://images.unsplash.com/photo-1546868871-7041f2a55e12',
    'https://images.unsplash.com/photo-1594938298603-c8148c4dae35',
    'https://images.unsplash.com/photo-1521572267360-ee0c2909d518',
    'https://images.unsplash.com/photo-1542291026-7eec264c27ff',
    'https://images.unsplash.com/photo-1555041469-a586c61ea9bc',
    'https://images.unsplash.com/photo-1583847268964-b28dc8f51f92'
]

BRANDS = ['Kadosh', 'Apex', 'Titan', 'Vanguard', 'ProLine', 'Evo', 'Nexus', 'UltraCraft', 'Zenith', 'Prime', 'Starlight', 'Omni', 'Velocity', 'Summit', 'Aero']
DESCRIPTORS = ['Pro', 'Ultra', 'Premium', 'Smart', 'Elite', 'Classic', 'Heavy-Duty', 'Compact', 'Ergonomic', 'Artisan', 'Performance', 'Deluxe', 'Essential', 'Gen-2', 'Modular']

class Command(BaseCommand):
    help = 'Generates products with 50+ main categories, 15 subcategories per category, and optional dataset clearing.'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=100000, help='Total number of products to generate (default: 100000)')
        parser.add_argument('--clear', '--delete-existing', action='store_true', help='Delete all existing products and categories before generation')
        parser.add_argument('--tenant-id', type=str, default=str(DEFAULT_TENANT_ID), help='Tenant ID to associate products with')

    def handle(self, *args, **options):
        total_target = options['count']
        clear_data = options['clear']
        tenant_uuid = uuid.UUID(options['tenant_id'])

        self.stdout.write(self.style.SUCCESS(f"Targeting Shop Tenant ID: {tenant_uuid}"))

        if clear_data:
            self.stdout.write(self.style.WARNING("Clearing existing catalog database records..."))
            ProductImage.objects.all().delete()
            ProductVariant.objects.all().delete()
            ProductPrice.objects.all().delete()
            Product.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Catalog records cleared successfully."))

        # 1. Build Categories & Subcategories
        self.stdout.write(self.style.SUCCESS(f"Creating 50+ Categories with 15 Subcategories each..."))
        subcat_objects = []

        for main_cat_name, subcat_list in CATEGORIES_TAXONOMY.items():
            parent_slug = slugify(main_cat_name)
            parent_cat, _ = Category.objects.get_or_create(
                tenant_id=tenant_uuid,
                slug=parent_slug,
                defaults={'name': main_cat_name, 'is_global': True}
            )

            for sub_name in subcat_list:
                sub_slug = slugify(f"{main_cat_name}-{sub_name}")
                sub_cat, _ = Category.objects.get_or_create(
                    tenant_id=tenant_uuid,
                    slug=sub_slug,
                    defaults={'name': sub_name, 'parent': parent_cat, 'is_global': True}
                )
                subcat_objects.append((parent_cat, sub_cat))

        num_subcats = len(subcat_objects)
        self.stdout.write(self.style.SUCCESS(f"Created {len(CATEGORIES_TAXONOMY)} Main Categories & {num_subcats} Subcategories."))

        # 2. High-Speed Bulk Generation of Products
        self.stdout.write(self.style.SUCCESS(f"Generating {total_target:,} products in high-speed batches..."))

        batch_size = 5000
        generated = 0
        product_seq = 1

        while generated < total_target:
            current_batch_target = min(batch_size, total_target - generated)
            products_to_create = []
            prices_to_create = []
            images_to_create = []
            variants_to_create = []

            for _ in range(current_batch_target):
                parent_cat, sub_cat = subcat_objects[(product_seq - 1) % num_subcats]
                brand = random.choice(BRANDS)
                desc = random.choice(DESCRIPTORS)
                prod_name = f"{brand} {desc} {sub_cat.name} #{product_seq}"
                sku = f"KAD-{slugify(sub_cat.name)[:6].upper()}-{product_seq:07d}"

                prod_id = uuid.uuid4()
                base_price = Decimal(str(round(random.uniform(9.99, 1999.99), 2)))
                cost_price = Decimal(str(round(float(base_price) * random.uniform(0.3, 0.65), 2)))

                # Product Object
                product = Product(
                    id=prod_id,
                    tenant_id=tenant_uuid,
                    name=prod_name,
                    sku=sku,
                    description=f"Premium {prod_name} engineered for superior quality, performance, and durability.",
                    category=parent_cat,
                    subcategory=sub_cat
                )
                products_to_create.append(product)

                # Price Detail
                prices_to_create.append(ProductPrice(
                    id=uuid.uuid4(),
                    product=product,
                    tenant_id=tenant_uuid,
                    base_price=base_price,
                    cost_price=cost_price,
                    currency='USD'
                ))

                # Primary & Secondary Images
                img_sample = random.choice(IMAGE_POOL)
                images_to_create.append(ProductImage(
                    id=uuid.uuid4(),
                    product=product,
                    tenant_id=tenant_uuid,
                    image_url=f"{img_sample}?w=800&auto=format&fit=crop&q=80&sig={product_seq}_1",
                    alt_text=f"{prod_name} Primary Image",
                    display_order=1,
                    is_primary=True
                ))
                images_to_create.append(ProductImage(
                    id=uuid.uuid4(),
                    product=product,
                    tenant_id=tenant_uuid,
                    image_url=f"{img_sample}?w=800&auto=format&fit=crop&q=80&sig={product_seq}_2",
                    alt_text=f"{prod_name} Secondary Image",
                    display_order=2,
                    is_primary=False
                ))

                # Variants
                variants_to_create.append(ProductVariant(
                    id=uuid.uuid4(),
                    product=product,
                    tenant_id=tenant_uuid,
                    sku=f"{sku}-STD",
                    price=base_price,
                    stock=random.randint(10, 500),
                    is_active=True
                ))
                variants_to_create.append(ProductVariant(
                    id=uuid.uuid4(),
                    product=product,
                    tenant_id=tenant_uuid,
                    sku=f"{sku}-PRO",
                    price=base_price + Decimal('25.00'),
                    stock=random.randint(5, 200),
                    is_active=True
                ))

                product_seq += 1

            # Bulk Inserts into DB
            Product.objects.bulk_create(products_to_create, batch_size=batch_size, ignore_conflicts=True)
            ProductPrice.objects.bulk_create(prices_to_create, batch_size=batch_size, ignore_conflicts=True)
            ProductImage.objects.bulk_create(images_to_create, batch_size=batch_size, ignore_conflicts=True)
            ProductVariant.objects.bulk_create(variants_to_create, batch_size=batch_size, ignore_conflicts=True)

            generated += current_batch_target
            self.stdout.write(f" -> Generated {generated:,} / {total_target:,} products...")

        self.stdout.write(self.style.SUCCESS(
            f"Successfully generated {total_target:,} products across {len(CATEGORIES_TAXONOMY)} categories and {num_subcats} subcategories for shop tenant {tenant_uuid}!"
        ))
