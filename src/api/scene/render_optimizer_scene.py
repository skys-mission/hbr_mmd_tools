# -*- coding: utf-8 -*-
# Copyright (c) 2026, https://github.com/skys-mission and Half-Bottled Reverie
"""
Render Optimizer Scene Properties
"""
import bpy  # pylint: disable=import-error

render_opt_style = bpy.props.EnumProperty(
    name="Toon Style",
    description="Cel shading style preset",
    items=[
        ('STANDARD', "Standard", "Classic two-tone anime shading"),
        ('SOFT', "Soft", "Softer three-tone shading with gentle shadows"),
        ('CONTRAST', "Contrast", "Hard two-tone shading with deep shadows"),
    ],
    default='STANDARD',
)

render_opt_outline = bpy.props.EnumProperty(
    name="Outline",
    description="Outline strategy",
    items=[
        ('SOLIDIFY', "Solidify (Fast)", "Inverted hull outline, real-time in EEVEE"),
        ('FREESTYLE', "Freestyle (Quality)", "Topology-aware line art, slower render"),
        ('NONE', "None", "No outline"),
    ],
    default='SOLIDIFY',
)

render_opt_outline_width = bpy.props.FloatProperty(
    name="Outline Width",
    description="Outline thickness multiplier (Solidify mode only)",
    default=0.25,
    min=0.2,
    max=5.0,
)

render_opt_use_compositor = bpy.props.BoolProperty(
    name="Compositor Post",
    description="Enable light bloom and contrast post-processing",
    default=True,
)

render_opt_brightness_override = bpy.props.EnumProperty(
    name="Brightness",
    description="Override automatic brightness detection",
    items=[
        ('AUTO', "Auto", "Automatically detect from model tone"),
        ('LIGHT', "Light", "Model is overall light-colored"),
        ('MEDIUM', "Medium", "Standard brightness"),
        ('DARK', "Dark", "Model is overall dark-colored"),
    ],
    default='AUTO',
)
