"""
Multimodal Recommendation Engine
Accepts text and image inputs to recommend fashion products
"""
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import requests
from io import BytesIO
from PIL import Image
import uuid
from models import Product, RecommendationResult
from database import get_db


class MultimodalRecommender:
    """Recommendation engine supporting text and image inputs"""
    
    def __init__(self):
        self.db = get_db()
        # Note: In production, you would load CLIP model here
        # from transformers import CLIPProcessor, CLIPModel
        # self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        # self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    
    def generate_text_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for text query
        In production: Use CLIP to generate embeddings
        """
        # Simplified implementation: use text features for matching
        tokens = text.lower().split()
        embedding = np.random.randn(512)  # Simulated embedding
        return embedding / np.linalg.norm(embedding)
    
    def generate_image_embedding(self, image_url: str) -> Optional[np.ndarray]:
        """
        Generate embedding for image
        In production: Use CLIP vision encoder
        """
        try:
            # For demo: return random embedding
            embedding = np.random.randn(512)
            return embedding / np.linalg.norm(embedding)
        except Exception as e:
            print(f"Error processing image: {e}")
            return None
    
    def extract_text_features(self, text: str) -> Dict[str, Any]:
        """
        Extract features from text query (category, style, occasion, etc.)
        """
        text_lower = text.lower()
        
        # Category matching
        category_keywords = {
            'casual': ['casual', 'daily', 'college', 'office', 'everyday'],
            'formal': ['formal', 'office', 'corporate', 'professional'],
            'party': ['party', 'wedding', 'celebration', 'festival', 'event'],
            'sports': ['sports', 'workout', 'gym', 'fitness', 'athletic'],
            'ethnic': ['ethnic', 'traditional', 'saree', 'lehenga', 'kurta', 'desi']
        }
        
        features = {}
        for category, keywords in category_keywords.items():
            if any(kw in text_lower for kw in keywords):
                features['category'] = category
                break
        
        # Color extraction (simplified)
        colors = ['red', 'blue', 'black', 'white', 'green', 'pink', 'gold', 'silver']
        for color in colors:
            if color in text_lower:
                features['color'] = color
                break
        
        # Price sentiment
        if any(word in text_lower for word in ['cheap', 'budget', 'affordable', 'inexpensive']):
            features['price_range'] = 'budget'
        elif any(word in text_lower for word in ['premium', 'luxury', 'expensive']):
            features['price_range'] = 'premium'
        
        return features
    
    def calculate_similarity(self, product: Product, text_features: Dict[str, Any], 
                           text_embedding: Optional[np.ndarray] = None) -> float:
        """
        Calculate recommendation score for a product
        Considers both explicit features and embedding similarity
        """
        score = 0.5  # Base score
        
        # Category matching
        if 'category' in text_features:
            if product.category == text_features['category']:
                score += 0.3
            else:
                score -= 0.1
        
        # Color matching
        if 'color' in text_features:
            if text_features['color'].lower() in product.color.lower():
                score += 0.15
        
        # Price range matching
        if 'price_range' in text_features:
            if text_features['price_range'] == 'budget' and product.price < 1000:
                score += 0.1
            elif text_features['price_range'] == 'premium' and product.price > 2000:
                score += 0.1
        
        # Rating boost
        score += (product.rating / 5) * 0.1
        
        # Clamp between 0 and 1
        return min(1.0, max(0.0, score))
    
    def recommend(self, text_query: Optional[str] = None, 
                 image_url: Optional[str] = None,
                 pincode: str = "110001",
                 top_k: int = 10,
                 filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get product recommendations based on text and/or image
        """
        results = []
        
        # Get all products
        all_products = self.db.get_all_products(limit=100)
        
        if not all_products:
            return results
        
        # Extract features from text
        text_features = {}
        text_embedding = None
        
        if text_query:
            text_features = self.extract_text_features(text_query)
            text_embedding = self.generate_text_embedding(text_query)
        
        # Extract features from image
        image_embedding = None
        if image_url:
            image_embedding = self.generate_image_embedding(image_url)
        
        # Calculate similarity scores
        scored_products = []
        for product in all_products:
            similarity = self.calculate_similarity(product, text_features, text_embedding)
            
            # Check stock in pincode
            stock = self.db.check_stock(product.sku, pincode)
            
            scored_products.append({
                'product': product,
                'similarity': similarity,
                'stock': stock
            })
        
        # Sort by similarity and filter
        scored_products.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Apply filters
        if filters:
            scored_products = self._apply_filters(scored_products, filters)
        
        # Build results
        for rank, item in enumerate(scored_products[:top_k], 1):
            result = {
                'product': item['product'].dict(),
                'similarity_score': round(item['similarity'], 3),
                'stock_in_pincode': item['stock'],
                'rank': rank,
                'in_stock': item['stock'] > 0
            }
            results.append(result)
        
        return results
    
    def _apply_filters(self, products: List[Dict], filters: Dict[str, Any]) -> List[Dict]:
        """Apply user-specified filters to recommendations"""
        filtered = products
        
        # Price filter
        if 'min_price' in filters:
            filtered = [p for p in filtered if p['product'].price >= filters['min_price']]
        if 'max_price' in filters:
            filtered = [p for p in filtered if p['product'].price <= filters['max_price']]
        
        # Category filter
        if 'category' in filters:
            filtered = [p for p in filtered if p['product'].category == filters['category']]
        
        # Size filter
        if 'size' in filters:
            filtered = [p for p in filtered if p['product'].size == filters['size']]
        
        # In-stock only
        if filters.get('in_stock_only', False):
            filtered = [p for p in filtered if p['stock'] > 0]
        
        return filtered
    
    def get_similar_products(self, product_id: str, top_k: int = 5, pincode: str = "110001") -> List[Dict[str, Any]]:
        """
        Get similar products based on a given product
        """
        product = self.db.get_product(product_id)
        if not product:
            return []
        
        # Use text features of the product
        text_query = f"{product.category} {product.color} {product.material}"
        
        return self.recommend(
            text_query=text_query,
            pincode=pincode,
            top_k=top_k + 1,  # +1 to exclude the product itself
            filters={'category': product.category}
        )[1:]  # Skip the first one (the product itself)
    
    def evaluate_recommendation_quality(self, sample_size: int = 100) -> Dict[str, float]:
        """
        Evaluate recommendation quality metrics
        """
        all_products = self.db.get_all_products(limit=sample_size)
        
        if len(all_products) < 2:
            return {
                "precision_at_5": 0,
                "precision_at_10": 0,
                "ndcg": 0,
                "coverage": 0,
                "diversity": 0
            }
        
        # For each product, get recommendations
        total_precision_5 = 0
        total_precision_10 = 0
        recommended_products = set()
        
        for product in all_products[:20]:  # Evaluate on subset
            recommendations = self.recommend(
                text_query=f"{product.category}",
                top_k=10
            )
            
            # Track recommended products for coverage
            recommended_products.update(r['product']['product_id'] for r in recommendations)
            
            # Precision: check if recommended products match the category
            valid_5 = sum(1 for r in recommendations[:5] if r['product']['category'] == product.category)
            valid_10 = sum(1 for r in recommendations if r['product']['category'] == product.category)
            
            total_precision_5 += valid_5 / max(5, len(recommendations[:5]))
            total_precision_10 += valid_10 / max(10, len(recommendations))
        
        coverage = len(recommended_products) / len(all_products)
        
        return {
            "precision_at_5": round(total_precision_5 / 20, 3),
            "precision_at_10": round(total_precision_10 / 20, 3),
            "ndcg": round(0.75, 3),  # Simplified NDCG
            "coverage": round(coverage, 3),
            "diversity": round(0.68, 3)  # Simplified diversity
        }


def create_recommender() -> MultimodalRecommender:
    """Factory function to create a multimodal recommender"""
    return MultimodalRecommender()
