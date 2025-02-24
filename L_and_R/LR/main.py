import qrcode
from PIL import Image
# UPI Payment URL
upi_id = "ishanraj845@okhdfcbank"
name = "Esan Raj"
# amount = "1000"
upi_url = f"upi://pay?pa={upi_id}&pn={name}&cu=INR"

# Generate QR Code

qr = qrcode.QRCode(
    version=5,
    error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction
    box_size=10,
    border=4,
)
qr.add_data(upi_url)
qr.make(fit=True)

# Create QR code image
qr_img = qr.make_image(fill="black", back_color="white").convert("RGB")

# Load the logo and remove transparency
logo_path = "mediport_icon.png"  # Update with your logo path
logo = Image.open(logo_path).convert("RGBA")
new_logo = Image.new("RGB", logo.size, "white")  # White background
new_logo.paste(logo, mask=logo.split()[3])  # Apply transparency mask
logo = new_logo  # Use the updated logo

# Resize the logo
logo_size = (qr_img.size[0] // 4, qr_img.size[1] // 4)  # 25% of QR size
logo = logo.resize(logo_size, Image.LANCZOS)

# Calculate logo position
pos = ((qr_img.size[0] - logo.size[0]) // 2, (qr_img.size[1] - logo.size[1]) // 2)

# Paste logo onto QR code
qr_img.paste(logo, pos)

# Save the final QR code
qr_img.save("custom_upi_qr.png")

print("Custom QR Code Generated: custom_upi_qr.png")
