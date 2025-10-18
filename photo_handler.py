"""
Photo handling module for uploading and processing user and partner photos
"""
import streamlit as st
from PIL import Image
import io
from typing import Optional, Tuple


class PhotoHandler:
    """Handles photo uploads and processing for user and partner profiles."""
    
    def __init__(self):
        self.allowed_types = ["jpg", "jpeg", "png", "gif", "webp"]
        self.max_size_mb = 10
    
    def validate_image(self, image_file) -> Tuple[bool, str]:
        """Validate uploaded image file."""
        try:
            # Check file extension
            file_extension = image_file.name.split('.')[-1].lower()
            if file_extension not in self.allowed_types:
                return False, f"File type {file_extension} not allowed. Allowed types: {', '.join(self.allowed_types)}"
            
            # Check file size
            image_file.seek(0, 2)  # Seek to end
            file_size = image_file.tell()
            image_file.seek(0)  # Reset to beginning
            
            if file_size > self.max_size_mb * 1024 * 1024:
                return False, f"File size too large. Maximum size: {self.max_size_mb}MB"
            
            # Try to open with PIL to validate it's a valid image
            image_file.seek(0)
            with Image.open(image_file) as img:
                img.verify()
            
            image_file.seek(0)  # Reset for actual use
            return True, "Valid image"
            
        except Exception as e:
            return False, f"Invalid image file: {str(e)}"
    
    def process_image(self, image_file, max_size: Tuple[int, int] = (200, 200)) -> Optional[bytes]:
        """Process and resize image for display."""
        try:
            image_file.seek(0)
            with Image.open(image_file) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize while maintaining aspect ratio
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Convert to bytes
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='JPEG', quality=85)
                img_bytes.seek(0)
                
                return img_bytes.getvalue()
                
        except Exception as e:
            st.error(f"Error processing image: {str(e)}")
            return None
    
    def upload_user_photo(self) -> Optional[bytes]:
        """Handle user photo upload."""
        uploaded_file = st.file_uploader(
            "Choose your photo",
            type=self.allowed_types,
            key="user_photo_uploader",
            help=f"Upload a photo of yourself (max {self.max_size_mb}MB)"
        )
        
        if uploaded_file:
            is_valid, message = self.validate_image(uploaded_file)
            if is_valid:
                processed_image = self.process_image(uploaded_file)
                if processed_image:
                    st.success("✅ Your photo uploaded successfully!")
                    return processed_image
            else:
                st.error(f"❌ {message}")
        
        return None
    
    def upload_partner_photo(self) -> Optional[bytes]:
        """Handle partner photo upload."""
        uploaded_file = st.file_uploader(
            "Choose partner's photo",
            type=self.allowed_types,
            key="partner_photo_uploader",
            help=f"Upload a photo of the person you want to chat with (max {self.max_size_mb}MB)"
        )
        
        if uploaded_file:
            is_valid, message = self.validate_image(uploaded_file)
            if is_valid:
                processed_image = self.process_image(uploaded_file)
                if processed_image:
                    st.success("✅ Partner photo uploaded successfully!")
                    return processed_image
            else:
                st.error(f"❌ {message}")
        
        return None
