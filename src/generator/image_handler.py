def generate_and_upload_image(self, prompt, topic):
    # Pake Pexels API (gratis, lebih reliable dari Unsplash)
    PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')  # Lo harus daftar dulu
    
    # Kalo ga ada Pexels, pake placeholder gambar dari Cloudinary
    if not PEXELS_API_KEY:
        # Bikin gambar placeholder pake Cloudinary
        placeholder_url = f"https://res.cloudinary.com/{os.getenv('CLOUDINARY_CLOUD_NAME')}/image/upload/w_1200,h_630,c_fill/v1/travel/{topic.replace(' ', '_')}"
        return placeholder_url
    
    # Pake Pexels API
    headers = {"Authorization": PEXELS_API_KEY}
    url = f"https://api.pexels.com/v1/search?query={topic}&per_page=1"
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data['photos']:
            image_url = data['photos'][0]['src']['large']
            # Upload ke Cloudinary
            upload_result = cloudinary.uploader.upload(image_url)
            return upload_result['secure_url']
    
    # Fallback: pake Unsplash dengan user-agent
    unsplash_url = f"https://source.unsplash.com/featured/1200x630/?{topic.replace(' ', ',')},travel"
    response = requests.get(unsplash_url, headers={'User-Agent': 'Mozilla/5.0'})
    img = Image.open(BytesIO(response.content))
    
    temp_path = f"/tmp/{topic.replace(' ', '_')}.jpg"
    img.save(temp_path)
    upload_result = cloudinary.uploader.upload(temp_path)
    os.remove(temp_path)
    return upload_result['secure_url']
