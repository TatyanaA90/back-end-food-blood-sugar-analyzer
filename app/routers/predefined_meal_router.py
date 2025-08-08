from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.predefined_meal import PredefinedMeal
from app.models.predefined_meal_ingredient import PredefinedMealIngredient
from app.models.user import User
from app.schemas.predefined_meal import (
    PredefinedMealCreate, PredefinedMealUpdate, PredefinedMealRead,
    PredefinedMealWithNutrition, MealFromPredefinedCreate
)
from app.core.security import get_current_user
from typing import List
from datetime import datetime, UTC

router = APIRouter(prefix="/predefined-meals", tags=["predefined-meals"])

def calculate_meal_nutrition(ingredients: List[PredefinedMealIngredient]) -> dict:
    """Calculate nutrition per portion for a predefined meal"""
    total_carbs = 0
    total_weight = 0
    total_gi = 0
    gi_count = 0
    
    for ingredient in ingredients:
        carbs = (ingredient.base_weight / 100) * ingredient.carbs_per_100g
        total_carbs += carbs
        total_weight += ingredient.base_weight
        
        if ingredient.glycemic_index is not None:
            total_gi += ingredient.glycemic_index
            gi_count += 1
    
    average_gi = total_gi / gi_count if gi_count > 0 else None
    
    return {
        "total_carbs_per_portion": round(total_carbs, 2),
        "total_weight_per_portion": round(total_weight, 2),
        "average_glycemic_index": round(average_gi, 2) if average_gi else None
    }

# Get all predefined meals (public, no auth required)
@router.get("/", response_model=List[PredefinedMealWithNutrition])
def list_predefined_meals(
    category: str = None,
    session: Session = Depends(get_session)
):
    """Get all active predefined meals, optionally filtered by category"""
    query = select(PredefinedMeal).where(PredefinedMeal.is_active == True)
    
    if category:
        query = query.where(PredefinedMeal.category == category)
    
    predefined_meals = session.exec(query).all()
    
    result = []
    for meal in predefined_meals:
        nutrition = calculate_meal_nutrition(meal.ingredients)
        result.append(PredefinedMealWithNutrition(
            id=meal.id,
            name=meal.name,
            description=meal.description,
            category=meal.category,
            ingredients=meal.ingredients,
            **nutrition
        ))
    
    return result

# Get a specific predefined meal
@router.get("/{meal_id}", response_model=PredefinedMealWithNutrition)
def get_predefined_meal(
    meal_id: int,
    session: Session = Depends(get_session)
):
    """Get a specific predefined meal by ID"""
    meal = session.get(PredefinedMeal, meal_id)
    if not meal or not meal.is_active:
        raise HTTPException(status_code=404, detail="Predefined meal not found")
    
    nutrition = calculate_meal_nutrition(meal.ingredients)
    return PredefinedMealWithNutrition(
        id=meal.id,
        name=meal.name,
        description=meal.description,
        category=meal.category,
        ingredients=meal.ingredients,
        **nutrition
    )

# Create a new predefined meal (admin only)
@router.post("/", response_model=PredefinedMealRead, status_code=status.HTTP_201_CREATED)
def create_predefined_meal(
    meal_data: PredefinedMealCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Create a new predefined meal (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can create predefined meals")
    
    # Validate quantity constraints
    for ingredient in meal_data.ingredients:
        if ingredient.base_weight < 0:
            raise HTTPException(status_code=400, detail="Ingredient weight must be >= 0")
        if ingredient.carbs_per_100g < 0:
            raise HTTPException(status_code=400, detail="Carbs per 100g must be >= 0")
    
    # Create the predefined meal
    meal = PredefinedMeal(
        name=meal_data.name,
        description=meal_data.description,
        category=meal_data.category,
        is_active=meal_data.is_active,
        created_by_admin=meal_data.created_by_admin
    )
    session.add(meal)
    session.commit()
    session.refresh(meal)
    
    # Create ingredients
    for ingredient_data in meal_data.ingredients:
        ingredient = PredefinedMealIngredient(
            predefined_meal_id=meal.id,
            name=ingredient_data.name,
            base_weight=ingredient_data.base_weight,
            carbs_per_100g=ingredient_data.carbs_per_100g,
            glycemic_index=ingredient_data.glycemic_index,
            note=ingredient_data.note
        )
        session.add(ingredient)
    
    session.commit()
    session.refresh(meal)
    return PredefinedMealRead.model_validate(meal)

# Update a predefined meal (admin only)
@router.put("/{meal_id}", response_model=PredefinedMealRead)
def update_predefined_meal(
    meal_id: int,
    meal_data: PredefinedMealUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update a predefined meal (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can update predefined meals")
    
    meal = session.get(PredefinedMeal, meal_id)
    if not meal:
        raise HTTPException(status_code=404, detail="Predefined meal not found")
    
    # Update meal fields
    for field, value in meal_data.model_dump(exclude_unset=True, exclude={'ingredients'}).items():
        setattr(meal, field, value)
    
    # Update ingredients if provided
    if meal_data.ingredients is not None:
        # Delete existing ingredients
        session.exec(select(PredefinedMealIngredient).where(
            PredefinedMealIngredient.predefined_meal_id == meal_id
        )).delete()
        
        # Create new ingredients
        for ingredient_data in meal_data.ingredients:
            ingredient = PredefinedMealIngredient(
                predefined_meal_id=meal.id,
                name=ingredient_data.name,
                base_weight=ingredient_data.base_weight,
                carbs_per_100g=ingredient_data.carbs_per_100g,
                glycemic_index=ingredient_data.glycemic_index,
                note=ingredient_data.note
            )
            session.add(ingredient)
    
    session.commit()
    session.refresh(meal)
    return PredefinedMealRead.model_validate(meal)

# Delete a predefined meal (admin only)
@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_predefined_meal(
    meal_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Delete a predefined meal (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can delete predefined meals")
    
    meal = session.get(PredefinedMeal, meal_id)
    if not meal:
        raise HTTPException(status_code=404, detail="Predefined meal not found")
    
    # Check if any user meals are using this template
    user_meals_count = len(meal.user_meals)
    if user_meals_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete predefined meal: {user_meals_count} user meals are using this template"
        )
    
    session.delete(meal)
    session.commit()
    return None

# Get meal categories
@router.get("/categories/list")
def get_meal_categories():
    """Get list of available meal categories"""
    return [
        "breakfast",
        "lunch", 
        "dinner",
        "snack",
        "dessert",
        "beverage"
    ]
