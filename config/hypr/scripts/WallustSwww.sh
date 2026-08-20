#!/bin/bash
# /* ---- 💫 https://github.com/JaKooLit 💫 ---- */  ##
# Wallust Colors for current wallpaper

# Define the path to the awww cache directory
# awww >= 0.12 nests the per-monitor cache under a version subdir (e.g. 0.12.1/DP-3)
cache_dir="$HOME/.cache/awww/"

# Initialize a flag to determine if the ln command was executed
ln_success=false

# Get current focused monitor
current_monitor=$(hyprctl monitors | awk '/^Monitor/{name=$2} /focused: yes/{print name}')
echo $current_monitor
# Find the newest cache file for the focused monitor, at any nesting depth
cache_file=$(find "$cache_dir" -name "$current_monitor" -type f -printf '%T@ %p\n' 2>/dev/null \
    | sort -rn | head -n 1 | cut -d' ' -f2-)
echo $cache_file
# Check if the cache file exists for the current monitor output
if [ -n "$cache_file" ] && [ -f "$cache_file" ]; then
    # Cache file is NUL-separated (e.g. "\0crop:center\0Lanczos3\0/path/to/img");
    # the image path is the last field
    wallpaper_path=$(tr '\0' '\n' < "$cache_file" | tail -n 1)
    echo $wallpaper_path
    # symlink the wallpaper to the location Rofi can access
    if ln -sf "$wallpaper_path" "$HOME/.config/rofi/.current_wallpaper"; then
        ln_success=true  # Set the flag to true upon successful execution
    fi
    # copy the wallpaper for wallpaper effects
	cp -r "$wallpaper_path" "$HOME/.config/hypr/wallpaper_effects/.wallpaper_current"
fi

# Check the flag before executing further commands
if [ "$ln_success" = true ]; then
    # execute wallust
	echo 'about to execute wallust'
    # execute wallust skipping tty and terminal changes
    wallust run "$wallpaper_path" -s &
fi
