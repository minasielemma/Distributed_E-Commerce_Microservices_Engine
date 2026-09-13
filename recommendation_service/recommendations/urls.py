from django.urls import path
from .views import (
    PersonalizedRecommendationsView,
    CopurchaseRecommendationsView,
    SimilarRecommendationsView,
    TrendingRecommendationsView,
    TrackViewApiView,
    RecommendedMerchantsView,
    RecommendedCategoriesView
)

urlpatterns = [
    path('personalized/', PersonalizedRecommendationsView.as_view(), name='recommendations-personalized'),
    path('copurchase/', CopurchaseRecommendationsView.as_view(), name='recommendations-copurchase'),
    path('similar/', SimilarRecommendationsView.as_view(), name='recommendations-similar'),
    path('trending/', TrendingRecommendationsView.as_view(), name='recommendations-trending'),
    path('merchants/', RecommendedMerchantsView.as_view(), name='recommendations-merchants'),
    path('categories/', RecommendedCategoriesView.as_view(), name='recommendations-categories'),
    path('track-view/', TrackViewApiView.as_view(), name='recommendations-track-view'),
]
