from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.meal import Meal
from app.models.meal_ingredient import MealIngredient
from app.models.user import User
from app.schemas import (
    MealCreate, MealUpdate, MealReadBasic, MealReadDetail,
    MealIngredientCreate, MealIngredientRead
)
from app.schemas.predefined_meal import MealFromPredefinedCreate
from app.models.predefined_meal import PredefinedMeal
from app.models.predefined_meal_ingredient import PredefinedMealIngredient
from app.core.security import get_current_user
from typing import List

router = APIRouter(prefix="/meals", tags=["meals"])

# Helper: check admin or owner
def can_edit_meal(meal: Meal, user: User) -> bool:
    return meal.user_id == user.id or user.is_admin

# Helper: calculate totals
def calculate_meal_totals(ingredients: List[MealIngredientCreate]):
    total_carbs = sum(i.carbs for i in ingredients)
    total_weight = sum(i.weight or 0 for i in ingredients)
    return total_carbs, total_weight

@router.post("/", response_model=MealReadDetail, status_code=status.HTTP_201_CREATED)
def create_meal(meal_in: MealCreate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    total_carbs, total_weight = calculate_meal_totals(meal_in.ingredients)
    assert current_user.id is not None, "User ID must not be None"
    meal = Meal(
        description=meal_in.description,
        total_weight=total_weight,
        total_carbs=total_carbs,
        glycemic_index=meal_in.glycemic_index,
        note=meal_in.note,
        photo_url=meal_in.photo_url,
        timestamp=meal_in.timestamp,
        user_id=current_user.id
    )
    session.add(meal)
    session.commit()
    session.refresh(meal)
    if meal.id is None:
        raise HTTPException(status_code=500, detail="Meal ID not set after creation.")
    # Add ingredients
    for ing in meal_in.ingredients:
        ingredient = MealIngredient(
            meal_id=int(meal.id),
            name=ing.name,
            weight=ing.weight,
            carbs=ing.carbs,
            glycemic_index=ing.glycemic_index,
            note=ing.note
        )
        session.add(ingredient)
    session.commit()
    session.refresh(meal)
    # Reload with ingredients
    meal = session.exec(select(Meal).where(Meal.id == meal.id)).first()
    return MealReadDetail.model_validate(meal)

@router.post("/from-predefined", response_model=MealReadDetail, status_code=status.HTTP_201_CREATED)
def create_meal_from_predefined(
    meal_data: MealFromPredefinedCreate, 
    session: Session = Depends(get_session), 
    current_user: User = Depends(get_current_user)
):
    """Create a meal from a predefined template with quantity and weight adjustments"""
    
    # Validate quantity
    if meal_data.quantity < 1 or meal_data.quantity > 10:
        raise HTTPException(status_code=400, detail="Quantity must be between 1 and 10")
    
    # Get the predefined meal
    predefined_meal = session.get(PredefinedMeal, meal_data.predefined_meal_id)
    if not predefined_meal or not predefined_meal.is_active:
        raise HTTPException(status_code=404, detail="Predefined meal not found")
    
    # Calculate base nutrition per portion
    total_carbs_per_portion = 0
    total_weight_per_portion = 0
    
    # Create ingredient adjustments map
    ingredient_adjustments = {}
    if meal_data.ingredient_adjustments:
        for adjustment in meal_data.ingredient_adjustments:
            ingredient_adjustments[adjustment['ingredient_id']] = adjustment['adjusted_weight']
    
    # Create meal ingredients from predefined template
    meal_ingredients = []
    for predefined_ingredient in predefined_meal.ingredients:
        # Calculate base weight for this portion
        base_weight = predefined_ingredient.base_weight * meal_data.quantity
        
        # Apply user adjustment if provided
        adjusted_weight = ingredient_adjustments.get(predefined_ingredient.id, base_weight)
        
        # Validate adjusted weight
        if adjusted_weight < 0:
            raise HTTPException(status_code=400, detail=f"Weight for {predefined_ingredient.name} must be >= 0")
        
        # Calculate carbs based on final weight
        carbs = (adjusted_weight / 100) * predefined_ingredient.carbs_per_100g
        
        total_carbs_per_portion += carbs
        total_weight_per_portion += adjusted_weight
        
        meal_ingredients.append({
            'name': predefined_ingredient.name,
            'weight': adjusted_weight,
            'carbs': carbs,
            'glycemic_index': predefined_ingredient.glycemic_index,
            'note': predefined_ingredient.note
        })
    
    # Create the meal
    assert current_user.id is not None, "User ID must not be None"
    meal = Meal(
        description=predefined_meal.name,
        total_weight=total_weight_per_portion,
        total_carbs=total_carbs_per_portion,
        note=meal_data.note,
        photo_url=meal_data.photo_url,
        timestamp=meal_data.timestamp,
        user_id=current_user.id,
        is_predefined=True,
        predefined_meal_id=predefined_meal.id,
        quantity=meal_data.quantity
    )
    session.add(meal)
    session.commit()
    session.refresh(meal)
    
    # Add ingredients
    if meal.id is None:
        raise HTTPException(status_code=500, detail="Meal ID not set after creation.")
    
    for ingredient_data in meal_ingredients:
        ingredient = MealIngredient(
            meal_id=int(meal.id),
            name=ingredient_data['name'],
            weight=ingredient_data['weight'],
            carbs=ingredient_data['carbs'],
            glycemic_index=ingredient_data['glycemic_index'],
            note=ingredient_data['note']
        )
        session.add(ingredient)
    
    session.commit()
    session.refresh(meal)
    
    # Reload with ingredients
    meal = session.exec(select(Meal).where(Meal.id == meal.id)).first()
    return MealReadDetail.model_validate(meal)

@router.get("/", response_model=List[MealReadBasic])
def list_meals(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    if current_user.is_admin:
        meals = session.exec(select(Meal)).all()
    else:
        meals = session.exec(select(Meal).where(Meal.user_id == current_user.id)).all()
    return [MealReadBasic.model_validate(m) for m in meals]

@router.get("/{meal_id}", response_model=MealReadDetail)
def get_meal(meal_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    meal = session.get(Meal, meal_id)
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    if not can_edit_meal(meal, current_user) and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    return MealReadDetail.model_validate(meal)

@router.put("/{meal_id}", response_model=MealReadDetail)
def update_meal(meal_id: int, meal_in: MealUpdate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    meal = session.get(Meal, meal_id)
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    if not can_edit_meal(meal, current_user):
        raise HTTPException(status_code=403, detail="Not authorized")
    # Update fields
    for field, value in meal_in.model_dump(exclude_unset=True).items():
        if field != "ingredients":
            setattr(meal, field, value)
    # Update ingredients if provided
    if meal_in.ingredients is not None:
        # Delete old ingredients
        old_ings = session.exec(select(MealIngredient).where(MealIngredient.meal_id == meal.id)).all()
        for ing in old_ings:
            session.delete(ing)
        # Add new ingredients
        assert meal.id is not None, "Meal ID must not be None"
        for ing in meal_in.ingredients:
            ingredient = MealIngredient(
                meal_id=int(meal.id),
                name=ing.name,
                weight=ing.weight,
                carbs=ing.carbs,
                glycemic_index=ing.glycemic_index,
                note=ing.note
            )
            session.add(ingredient)
        # Recalculate totals
        total_carbs, total_weight = calculate_meal_totals(meal_in.ingredients)
        meal.total_carbs = total_carbs
        meal.total_weight = total_weight
    session.commit()
    session.refresh(meal)
    return MealReadDetail.model_validate(meal)

@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meal(meal_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    meal = session.get(Meal, meal_id)
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    if not can_edit_meal(meal, current_user):
        raise HTTPException(status_code=403, detail="Not authorized")
    # Cascade delete ingredients
    assert meal.id is not None, "Meal ID must not be None"
    ingredients = session.exec(select(MealIngredient).where(MealIngredient.meal_id == int(meal.id))).all()
    for ing in ingredients:
        session.delete(ing)
    session.delete(meal)
    session.commit()
    return None
