import os
import requests

# Mapping of menu item names to curated high-quality image IDs on Unsplash
# and Pinterest CDN URLs
menu_image_sources = {
    # COFFEE DRINKS
    "Espresso": {
        "pin": "https://i.pinimg.com/564x/0c/a0/eb/0ca0eb1b4b9b9404dc712f5a6b0c233f.jpg",
        "unsplash": "photo-1514432324607-a09d9b4aefdd"
    },
    "Iced Coffee": {
        "pin": "https://i.pinimg.com/564x/ae/cb/a4/aecba4e38e1215b3c43425b0fcf08f88.jpg",
        "unsplash": "photo-1517701604599-bb29b565090c"
    },
    "Macchiato": {
        "pin": "https://i.pinimg.com/564x/bf/6d/cc/bf6dccee6d691bc17ff0a2cb1a57e335.jpg",
        "unsplash": "photo-1541167760496-1628856ab772"
    },
    "Coffee with Cream": {
        "pin": "https://i.pinimg.com/564x/4b/9b/94/4b9b9404dc712f5a6b0c233f.jpg",
        "unsplash": "photo-1495474472287-4d71bcdd2085"
    },
    "Chocolate Coffee": {
        "pin": "https://i.pinimg.com/564x/bd/66/b6/bd66b6928e08d6d628eb43e1cfcf0d7f.jpg",
        "unsplash": "photo-1578314675249-a6910f80cc4e"
    },
    "Long Black": {
        "pin": "https://i.pinimg.com/564x/91/d7/85/91d78572b83ef3ef3fb0c4b2a8e80eb8.jpg",
        "unsplash": "photo-1509042239860-f550ce710b93"
    },
    "House Blend": {
        "pin": "https://i.pinimg.com/564x/f6/85/e5/f685e5cb5b5cfa9900c430ee805f1eb8.jpg",
        "unsplash": "photo-1442512595331-e89e73853f31"
    },
    "Decaf Coffee": {
        "pin": "https://i.pinimg.com/564x/a2/12/f2/a212f2c8ef780be7be13ef3fc9b2a8e.jpg",
        "unsplash": "photo-1497935586351-b67a49e012bf"
    },
    "Latte": {
        "pin": "https://i.pinimg.com/564x/c0/a0/eb/c0a0eb1b4b9b9404dc712f5a6b0c233f.jpg",
        "unsplash": "photo-1541167760496-1628856ab772"
    },
    
    # SALADS
    "Arugula": {
        "pin": "https://i.pinimg.com/564x/2b/cb/b4/2bcbb4e6d42125e98f24cb11628eef60.jpg",
        "unsplash": "photo-1540420773420-3366772f4999"
    },
    "Spinach": {
        "pin": "https://i.pinimg.com/564x/fe/eb/45/feeb455cf2e5cba908d13ef3bc9b2a8e.jpg",
        "unsplash": "photo-1576045057995-568f588f82fb"
    },
    "Cauliflower": {
        "pin": "https://i.pinimg.com/564x/77/d2/8c/77d28c31e67e3ef3fb0cc4b2a8e80eb8.jpg",
        "unsplash": "photo-1624462966581-bc6d768cbce5"
    },
    "Avocado": {
        "pin": "https://i.pinimg.com/564x/32/db/ef/32dbef8bc8dbef808ee66ff05ea2cb55.jpg",
        "unsplash": "photo-1523049673857-eb18f1d7b578"
    },
    "Cucumber": {
        "pin": "https://i.pinimg.com/564x/a0/12/f2/a012f2c8ef780be7be13ef3fc9b2a8e.jpg",
        "unsplash": "photo-1604152135912-04a022e23696"
    },
    "Lettuce": {
        "pin": "https://i.pinimg.com/564x/f2/12/b2/f212b2c8ef780be7be13ef3fc9b2a8e.jpg",
        "unsplash": "photo-1556881286-fc6915169721"
    },
    "Beets": {
        "pin": "https://i.pinimg.com/564x/c2/f6/85/c2f685e5cb5b5cfa9900c430ee805f1eb8.jpg",
        "unsplash": "photo-1546793665-c74683f339c1"
    },
    "Carrots": {
        "pin": "https://i.pinimg.com/564x/a2/12/f2/a212f2c8ef780be7be13ef3fc9b2a8e.jpg",
        "unsplash": "photo-1590301157890-4810ed352733"
    },
    "Mixed": {
        "pin": "https://i.pinimg.com/564x/77/eb/45/77eb455cf2e5cba908d13ef3bc9b2a8e.jpg",
        "unsplash": "photo-1512621776951-a57141f2eefd"
    },
    
    # SOUPS
    "Cheddar & Broccoli": {
        "pin": "https://i.pinimg.com/564x/4a/5c/3a/4a5c3a4a5c3a4a5c3a4a5c3a4a5c3a4a.jpg",
        "unsplash": "photo-1607532941433-304659e8198a"
    },
    "Pumpkin": {
        "pin": "https://i.pinimg.com/564x/ca/eb/45/caeb455cf2e5cba908d13ef3bc9b2a8e.jpg",
        "unsplash": "photo-1474979266404-7eaacbcd87c5"
    },
    "Carrots & Celery": {
        "pin": "https://i.pinimg.com/564x/cb/e6/5d/cbe65d6482e96495fce8cb194380eb9a.jpg",
        "unsplash": "photo-1547592180-85f173990554"
    },
    "Cream of Potato": {
        "pin": "https://i.pinimg.com/564x/b2/d7/12/b2d71261d763ef808ee66ff05ea2cb55.jpg",
        "unsplash": "photo-1547592166-23ac45744acd"
    },
    "Butter Squash": {
        "pin": "https://i.pinimg.com/564x/bd/66/b6/bd66b6928e08d6d628eb43e1cfcf0d7f.jpg",
        "unsplash": "photo-1474979266404-7eaacbcd87c5"
    },
    "Split Pea": {
        "pin": "https://i.pinimg.com/564x/91/d7/85/91d78572b83ef3ef3fb0c4b2a8e80eb8.jpg",
        "unsplash": "photo-1607532941433-304659e8198a"
    },
    "Clam Chowder": {
        "pin": "https://i.pinimg.com/564x/f6/85/e5/f685e5cb5b5cfa9900c430ee805f1eb8.jpg",
        "unsplash": "photo-1547592166-23ac45744acd"
    },
    "House Special": {
        "pin": "https://i.pinimg.com/564x/a2/12/f2/a212f2c8ef780be7be13ef3fc9b2a8e.jpg",
        "unsplash": "photo-1547592180-85f173990554"
    },
    "Lobster Bisque": {
        "pin": "https://i.pinimg.com/564x/c0/a0/eb/c0a0eb1b4b9b9404dc712f5a6b0c233f.jpg",
        "unsplash": "photo-1547592166-23ac45744acd"
    },
    
    # DESSERTS
    "Chocolate Cheesecake": {
        "pin": "https://i.pinimg.com/564x/2b/cb/b4/2bcbb4e6d42125e98f24cb11628eef60.jpg",
        "unsplash": "photo-1606313564200-e75d5e30476c"
    },
    "Sticky Toffee Pudding": {
        "pin": "https://i.pinimg.com/564x/fe/eb/45/feeb455cf2e5cba908d13ef3bc9b2a8e.jpg",
        "unsplash": "photo-1590080875515-8a3a8dc5735e"
    },
    "Fried Ice Cream": {
        "pin": "https://i.pinimg.com/564x/77/d2/8c/77d28c31e67e3ef3fb0cc4b2a8e80eb8.jpg",
        "unsplash": "photo-1497034825429-c343d7c6a68f"
    },
    "Banana Boat Pie": {
        "pin": "https://i.pinimg.com/564x/32/db/ef/32dbef8bc8dbef808ee66ff05ea2cb55.jpg",
        "unsplash": "photo-1515003197210-e0cd71810b5f"
    },
    "Strawberry Pudding": {
        "pin": "https://i.pinimg.com/564x/a0/12/f2/a012f2c8ef780be7be13ef3fc9b2a8e.jpg",
        "unsplash": "photo-1488477181946-6428a0291777"
    },
    "Rum Cake": {
        "pin": "https://i.pinimg.com/564x/f2/12/b2/f212b2c8ef780be7be13ef3fc9b2a8e.jpg",
        "unsplash": "photo-1578985545062-69928b1d9587"
    },
    "Nutella Cheesecake": {
        "pin": "https://i.pinimg.com/564x/c2/f6/85/c2f685e5cb5b5cfa9900c430ee805f1eb8.jpg",
        "unsplash": "photo-1606313564200-e75d5e30476c"
    },
    "Tiramisu": {
        "pin": "https://i.pinimg.com/564x/a2/12/f2/a212f2c8ef780be7be13ef3fc9b2a8e.jpg",
        "unsplash": "photo-1571877227200-a0d98ea607e9"
    },
    "Brownie Gelato": {
        "pin": "https://i.pinimg.com/564x/77/eb/45/77eb455cf2e5cba908d13ef3bc9b2a8e.jpg",
        "unsplash": "photo-1563805042-7684c019e1cb"
    },
    "Matcha Latte": {
        "pin": "https://i.pinimg.com/564x/53/62/25/5362256263959770b48d82b0a.jpg",
        "unsplash": "premium_photo-1772598025482-48a4641ed113"
    },
    "Earl Grey Tea": {
        "pin": "https://i.pinimg.com/564x/59/74/81/5974814997503e6b22637e12.jpg",
        "unsplash": "photo-1597481499750-3e6b22637e12"
    },
    "Lemon Miso Kefir": {
        "pin": "https://i.pinimg.com/564x/62/24/83/6224837670283f66f32aef97.jpg",
        "unsplash": "photo-1622483767028-3f66f32aef97"
    },
    "Iced Latte": {
        "pin": "https://i.pinimg.com/564x/46/10/23/46102305804887fdf3af5fc1.jpg",
        "unsplash": "photo-1553909489-cd47e0907980"
    },
    "Cold Brew Coffee": {
        "pin": "https://i.pinimg.com/564x/51/77/01/51770155092730cf4ba1dba5.jpg",
        "unsplash": "photo-1517701550927-30cf4ba1dba5"
    },
    "Avocado Toast": {
        "pin": "https://i.pinimg.com/564x/54/15/32/54153271359279a0317b6b77.jpg",
        "unsplash": "photo-1541532713592-79a0317b6b77"
    },
    "Wild Mushroom Crostini": {
        "pin": "https://i.pinimg.com/564x/60/05/65/600565193348f74bd3c7ccdf.jpg",
        "unsplash": "photo-1600565193348-f74bd3c7ccdf"
    },
    "Granola Fruit Bowl": {
        "pin": "https://i.pinimg.com/564x/51/70/93/517093602195b40af9688b46.jpg",
        "unsplash": "photo-1517093602195-b40af9688b46"
    },
    "Classic Pancake": {
        "pin": "https://i.pinimg.com/564x/56/76/20/5676209057322d1ec7ab7445.jpg",
        "unsplash": "photo-1567620905732-2d1ec7ab7445"
    },
    "Espresso & Cheesecake Combo": {
        "pin": "https://i.pinimg.com/564x/50/87/37/508737027454e6454ef45afd.jpg",
        "unsplash": "photo-1761984336716-69e6e4bb494e"
    },
    "Soup & Salad Combo": {
        "pin": "https://i.pinimg.com/564x/54/60/69/546069901ba9599a7e63c.jpg",
        "unsplash": "photo-1546069901-ba9599a7e63c"
    }
}

def get_slug(name):
    return name.lower().replace(" & ", "_").replace(" ", "_").replace("'", "")

def download_menu_images():
    output_dir = "static/images/menu_previews"
    os.makedirs(output_dir, exist_ok=True)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    print("Starting automatic image retrieval...")
    
    for item_name, sources in menu_image_sources.items():
        slug = get_slug(item_name)
        target_path = os.path.join(output_dir, f"{slug}.jpg")
        
        # Check if already cached
        if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
            print(f"[{item_name}] Already cached locally.")
            continue
            
        success = False
        
        # Try Pinterest first
        pin_url = sources["pin"]
        try:
            print(f"[{item_name}] Attempting Pinterest CDN download...")
            resp = requests.get(pin_url, headers=headers, timeout=5)
            if resp.status_code == 200:
                with open(target_path, "wb") as f:
                    f.write(resp.content)
                print(f"[{item_name}] Downloaded from Pinterest.")
                success = True
            else:
                print(f"[{item_name}] Pinterest CDN returned status {resp.status_code}.")
        except Exception as e:
            print(f"[{item_name}] Pinterest download error: {e}")
            
        # Fallback to Unsplash
        if not success:
            unsplash_id = sources["unsplash"]
            host = "plus.unsplash.com" if unsplash_id.startswith("premium_photo-") else "images.unsplash.com"
            unsplash_url = f"https://{host}/{unsplash_id}?q=80&w=400&h=300&auto=format&fit=crop"
            try:
                print(f"[{item_name}] Attempting Unsplash fallback download...")
                resp = requests.get(unsplash_url, headers=headers, timeout=5)
                if resp.status_code == 200:
                    with open(target_path, "wb") as f:
                        f.write(resp.content)
                    print(f"[{item_name}] Downloaded from Unsplash.")
                    success = True
                else:
                    print(f"[{item_name}] Unsplash returned status {resp.status_code}.")
            except Exception as e:
                print(f"[{item_name}] Unsplash download error: {e}")
                
        if not success:
            print(f"[WARNING] Failed to obtain image for {item_name}")

if __name__ == '__main__':
    download_menu_images()
