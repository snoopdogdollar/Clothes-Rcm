"""
SQLAlchemy ORM models for clothing items and colors
"""

from sqlalchemy import Column, Integer, String, Text, DECIMAL, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from utils.database import Base

class ClothingItem(Base):
    """
    Main table for clothing items with AI results and user data
    """
    __tablename__ = 'clothing_items'
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # File references
    filename = Column(String(255), nullable=False)
    original_image_path = Column(Text, nullable=False)
    segmented_image_path = Column(Text)
    
    # AI Classification Results
    category = Column(String(100), index=True)
    confidence = Column(DECIMAL(5, 4))  # e.g., 0.8945
    
    # AI Color Analysis
    primary_color = Column(String(50), index=True)
    palette_type = Column(String(50))  # e.g., "Cool Palette", "Warm Palette"
    
    # User Input Data
    material = Column(String(100))
    size = Column(String(20))
    brand = Column(String(100))
    purchase_date = Column(Date)
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    colors = relationship(
        "ItemColor",
        back_populates="item",
        cascade="all, delete-orphan"  # Delete colors when item is deleted
    )
    
    def to_dict(self, include_colors=True):
        """
        Convert model instance to dictionary
        
        Args:
            include_colors: Whether to include related colors
        
        Returns:
            Dictionary representation of the item
        """
        data = {
            'id': self.id,
            'filename': self.filename,
            'original_image_path': self.original_image_path,
            'segmented_image_path': self.segmented_image_path,
            'category': self.category,
            'confidence': float(self.confidence) if self.confidence else None,
            'primary_color': self.primary_color,
            'palette_type': self.palette_type,
            'material': self.material,
            'size': self.size,
            'brand': self.brand,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_colors:
            data['colors'] = [color.to_dict() for color in self.colors]
        
        return data

class ItemColor(Base):
    """
    Table for storing multiple colors per item with percentages
    """
    __tablename__ = 'item_colors'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Foreign key
    item_id = Column(
        Integer,
        ForeignKey('clothing_items.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Color data
    color_name = Column(String(50), nullable=False)
    color_hex = Column(String(7), nullable=False)  # e.g., "#FF5733"
    color_rgb = Column(JSONB, nullable=False)  # e.g., {"r": 255, "g": 87, "b": 51}
    percentage = Column(DECIMAL(5, 2), nullable=False)  # e.g., 67.30
    
    # Relationship
    item = relationship("ClothingItem", back_populates="colors")
    
    def to_dict(self):
        """Convert model instance to dictionary"""
        return {
            'id': self.id,
            'color_name': self.color_name,
            'color_hex': self.color_hex,
            'color_rgb': self.color_rgb,
            'percentage': float(self.percentage) if self.percentage else None
        }
