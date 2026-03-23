import React from 'react';
import { 
  Utensils, 
  Car, 
  Film, 
  Home, 
  ShoppingBag, 
  Activity, 
  BookOpen, 
  Lightbulb, 
  Zap, 
  Box, 
  HelpCircle,
  Repeat
} from 'lucide-react';

interface CategoryIconProps {
  name?: string;
  className?: string;
}

const iconMap: Record<string, React.ElementType> = {
  'utensils': Utensils,
  'car': Car,
  'film': Film,
  'home': Home,
  'shopping-bag': ShoppingBag,
  'activity': Activity,
  'book-open': BookOpen,
  'lightbulb': Lightbulb,
  'zap': Zap,
  'box': Box,
  'repeat': Repeat,
  // Add fallback or aliases if needed
};

export default function CategoryIcon({ name, className = "w-5 h-5" }: CategoryIconProps) {
  const IconComponent = name ? (iconMap[name.toLowerCase()] || HelpCircle) : Zap; // Using Zap as default fallback as seen in other components
  
  return <IconComponent className={className} />;
}
