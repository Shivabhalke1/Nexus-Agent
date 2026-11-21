"""Product and category catalog endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.models import Category, Product
from app.schemas.response import APIResponse, PaginatedResponse
from app.schemas.category import CategoryResponse
from app.schemas.product import ProductResponse

router = APIRouter(prefix="/products", tags=["Catalog & Products"])


@router.get("/categories", response_model=APIResponse[List[CategoryResponse]])
def list_categories(db: Session = Depends(get_db)):
    """Retrieve all available product categories."""
    categories = db.query(Category).order_by(Category.name.asc()).all()
    return APIResponse(
        success=True,
        message="Categories retrieved successfully",
        data=[CategoryResponse.model_validate(c) for c in categories],
    )


@router.get("", response_model=APIResponse[PaginatedResponse[ProductResponse]])
def list_products(
    category: Optional[str] = Query(None, description="Filter by category slug"),
    search: Optional[str] = Query(None, description="Search term in product name or description"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Retrieve paginated product catalog with category and search filtering."""
    query = db.query(Product).options(joinedload(Product.category)).filter(Product.is_active == True)

    if category:
        query = query.join(Product.category).filter(Category.slug == category)

    if search:
        search_filter = f"%{search}%"
        query = query.filter((Product.name.ilike(search_filter)) | (Product.description.ilike(search_filter)))

    total = query.count()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    offset = (page - 1) * page_size
    products = query.order_by(Product.id.asc()).offset(offset).limit(page_size).all()

    paginated_data = PaginatedResponse(
        items=[ProductResponse.model_validate(p) for p in products],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )

    return APIResponse(
        success=True,
        message="Products retrieved successfully",
        data=paginated_data,
    )


@router.get("/{slug}", response_model=APIResponse[ProductResponse])
def get_product_by_slug(slug: str, db: Session = Depends(get_db)):
    """Retrieve single product details by slug."""
    product = (
        db.query(Product)
        .options(joinedload(Product.category))
        .filter(Product.slug == slug, Product.is_active == True)
        .first()
    )
    if not product:
        raise NotFoundException(resource="Product", identifier=slug)

    return APIResponse(
        success=True,
        message="Product details retrieved successfully",
        data=ProductResponse.model_validate(product),
    )
