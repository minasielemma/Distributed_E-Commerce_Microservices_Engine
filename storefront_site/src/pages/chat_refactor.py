import re

with open("ChatPage.jsx", "r") as f:
    content = f.read()

# 1. Imports
if "import { useLocation } from 'react-router-dom';" not in content:
    content = content.replace(
        "import { Link } from 'react-router-dom';",
        "import { Link, useLocation } from 'react-router-dom';"
    )
    if "useLocation" not in content:
        content = content.replace(
            "import React, { useState, useEffect, useLayoutEffect, useRef, useContext, useCallback } from 'react';",
            "import React, { useState, useEffect, useLayoutEffect, useRef, useContext, useCallback } from 'react';\nimport { useLocation } from 'react-router-dom';"
        )

# 2. Add query param processing
if "const location = useLocation();" not in content:
    content = content.replace(
        "export const ChatPage = () => {\n  const { user } = useContext(AuthContext);",
        "export const ChatPage = () => {\n  const { user } = useContext(AuthContext);\n  const location = useLocation();\n  const queryParams = new URLSearchParams(location.search);\n  const initialOrderId = queryParams.get('orderId');"
    )

if "useEffect(() => {\n    fetchRooms();\n  }, []);" in content:
    content = content.replace(
        "useEffect(() => {\n    fetchRooms();\n  }, []);",
        "useEffect(() => {\n    fetchRooms().then(() => {\n      if (initialOrderId) {\n        setModalError('');\n        setShowCreateModal(true);\n        setNewRoomType('ORDER_SUPPORT');\n        setSelectedOrder(initialOrderId);\n        setNewRoomName(`Order Support #${String(initialOrderId).substring(0, 8)}`);\n        fetchOrdersForPicker();\n        fetchShopsForPicker();\n      }\n    });\n  }, [initialOrderId]);"
    )

# 3. Class replacements
replacements = {
    "text-white": "text-[#111]",
    "bg-slate-950/40": "bg-[#F0F2F2]",
    "border-white/10": "border-[#D5D9D9]",
    "bg-slate-900/80": "bg-white",
    "bg-slate-900/30": "bg-white",
    "bg-slate-900": "bg-white",
    "bg-slate-950/80": "bg-white",
    "bg-slate-950/60": "bg-[#F0F2F2]",
    "bg-slate-950/90": "bg-white",
    "bg-slate-950": "bg-white",
    "bg-slate-800/90": "bg-[#F0F2F2]",
    "bg-slate-800/60": "bg-[#F0F2F2]",
    "bg-slate-800": "bg-[#F0F2F2]",
    "border-white/5": "border-[#D5D9D9]",
    "border-white/15": "border-[#D5D9D9]",
    "border-white/20": "border-[#D5D9D9]",
    "text-slate-400": "text-[#565959]",
    "text-slate-300": "text-[#565959]",
    "text-slate-500": "text-[#565959]",
    "text-slate-200": "text-[#111]",
    "text-indigo-400": "text-[#007185]",
    "text-indigo-300": "text-[#007185]",
    "text-indigo-200": "text-[#007185]",
    "bg-indigo-600/20": "bg-[#F0F2F2]",
    "bg-indigo-600/30": "bg-[#F0F2F2]",
    "border-indigo-500/30": "border-[#D5D9D9]",
    "border-indigo-500": "border-amazon-orange",
    "hover:bg-white/5": "hover:bg-[#F3F3F3]",
    "hover:text-white": "hover:text-[#111]",
    "hover:bg-indigo-500": "hover:bg-amazon-orange/90",
    "hover:bg-white/10": "hover:bg-[#F0F2F2]",
    "bg-white/5": "bg-[#F3F3F3]",
    "shadow-indigo-500/25": "shadow-sm",
    "bg-indigo-600": "bg-amazon-orange",
    "bg-indigo-500": "bg-amazon-orange",
    "bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500": "btn-buy-now",
    "glass-panel": "bg-white border border-[#D5D9D9] rounded-lg",
    "bg-black/70": "bg-black/50",
    "text-rose-300": "text-[#B12704]",
    "bg-rose-500/10": "bg-[#FFF]",
    "border-rose-500/30": "border-[#B12704]",
    "bg-amber-500/10": "bg-[#FFF]",
    "text-amber-300": "text-[#111]",
    "border-amber-500/30": "border-[#D5D9D9]",
    "text-amber-400/80": "text-[#565959]",
    "hover:bg-amber-600/20": "hover:bg-[#F0F2F2]",
    "bg-indigo-950/60": "bg-[#F0F2F2]",
    "text-indigo-300/70": "text-[#007185]",
    "bg-black/25": "bg-[#F0F2F2]"
}

# Apply replacements specifically inside className strings if possible, 
# but a global replace is acceptable since it's tailwind classes.
for old, new in replacements.items():
    content = content.replace(old, new)

# Let's fix some specific ones that might have conflicts
content = content.replace('bg-amazon-orange text-[#111] rounded-tr-none shadow-lg shadow-sm ml-auto', 'bg-[#F0F2F2] text-[#111] rounded-tr-none shadow-sm ml-auto')

with open("ChatPage.jsx", "w") as f:
    f.write(content)

