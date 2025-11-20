from pathlib import Path
from PIL import Image, ImageFilter
from typing import Optional


def get_image_info(image_path: str) -> dict:
    """
    Get information about an image file.

    Args:
        image_path: Path to the image file

    Returns:
        Dictionary with image information (width, height, format, mode)
    """
    try:
        with Image.open(image_path) as img:
            return {
                "success": True,
                "path": image_path,
                "width": img.width,
                "height": img.height,
                "format": img.format,
                "mode": img.mode,
                "size_bytes": Path(image_path).stat().st_size,
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


def resize_image(
    image_path: str, width: int, height: int, output_path: Optional[str] = None
) -> dict:
    """
    Resize an image to specified dimensions.

    Args:
        image_path: Path to the input image
        width: Target width in pixels
        height: Target height in pixels
        output_path: Path to save resized image (optional, defaults to input_resized.ext)

    Returns:
        Dictionary with operation result
    """
    try:
        with Image.open(image_path) as img:
            resized = img.resize((width, height), Image.Resampling.LANCZOS)

            if output_path is None:
                path = Path(image_path)
                output_path = str(path.parent / f"{path.stem}_resized{path.suffix}")

            resized.save(output_path)

            return {
                "success": True,
                "input": image_path,
                "output": output_path,
                "original_size": f"{img.width}x{img.height}",
                "new_size": f"{width}x{height}",
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


def convert_format(
    image_path: str, target_format: str, output_path: Optional[str] = None
) -> dict:
    """
    Convert image to a different format.

    Args:
        image_path: Path to the input image
        target_format: Target format (e.g., 'JPEG', 'PNG', 'WEBP')
        output_path: Path to save converted image (optional)

    Returns:
        Dictionary with operation result
    """
    try:
        with Image.open(image_path) as img:
            # Convert RGBA to RGB for JPEG
            if target_format.upper() == "JPEG" and img.mode == "RGBA":
                img = img.convert("RGB")

            if output_path is None:
                path = Path(image_path)
                ext = "." + target_format.lower().replace("jpeg", "jpg")
                output_path = str(path.parent / f"{path.stem}_converted{ext}")

            img.save(output_path, format=target_format.upper())

            return {
                "success": True,
                "input": image_path,
                "output": output_path,
                "original_format": img.format,
                "new_format": target_format.upper(),
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


def rotate_image(
    image_path: str, degrees: float, output_path: Optional[str] = None
) -> dict:
    """
    Rotate an image by specified degrees.

    Args:
        image_path: Path to the input image
        degrees: Rotation angle in degrees (counter-clockwise)
        output_path: Path to save rotated image (optional)

    Returns:
        Dictionary with operation result
    """
    try:
        with Image.open(image_path) as img:
            rotated = img.rotate(degrees, expand=True)

            if output_path is None:
                path = Path(image_path)
                output_path = str(path.parent / f"{path.stem}_rotated{path.suffix}")

            rotated.save(output_path)

            return {
                "success": True,
                "input": image_path,
                "output": output_path,
                "rotation": f"{degrees}°",
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


def crop_image(
    image_path: str,
    left: int,
    top: int,
    right: int,
    bottom: int,
    output_path: Optional[str] = None,
) -> dict:
    """
    Crop an image to specified coordinates.

    Args:
        image_path: Path to the input image
        left: Left coordinate
        top: Top coordinate
        right: Right coordinate
        bottom: Bottom coordinate
        output_path: Path to save cropped image (optional)

    Returns:
        Dictionary with operation result
    """
    try:
        with Image.open(image_path) as img:
            cropped = img.crop((left, top, right, bottom))

            if output_path is None:
                path = Path(image_path)
                output_path = str(path.parent / f"{path.stem}_cropped{path.suffix}")

            cropped.save(output_path)

            return {
                "success": True,
                "input": image_path,
                "output": output_path,
                "original_size": f"{img.width}x{img.height}",
                "cropped_size": f"{right-left}x{bottom-top}",
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


def apply_filter(
    image_path: str, filter_type: str, output_path: Optional[str] = None
) -> dict:
    """
    Apply a filter to an image.

    Args:
        image_path: Path to the input image
        filter_type: Type of filter ('blur', 'sharpen', 'grayscale', 'contour', 'detail', 'edge_enhance')
        output_path: Path to save filtered image (optional)

    Returns:
        Dictionary with operation result
    """
    try:
        with Image.open(image_path) as img:
            if filter_type.lower() == "grayscale":
                filtered = img.convert("L")
            elif filter_type.lower() == "blur":
                filtered = img.filter(ImageFilter.BLUR)
            elif filter_type.lower() == "sharpen":
                filtered = img.filter(ImageFilter.SHARPEN)
            elif filter_type.lower() == "contour":
                filtered = img.filter(ImageFilter.CONTOUR)
            elif filter_type.lower() == "detail":
                filtered = img.filter(ImageFilter.DETAIL)
            elif filter_type.lower() == "edge_enhance":
                filtered = img.filter(ImageFilter.EDGE_ENHANCE)
            else:
                return {
                    "success": False,
                    "error": f"Unknown filter type: {filter_type}",
                }

            if output_path is None:
                path = Path(image_path)
                output_path = str(
                    path.parent / f"{path.stem}_{filter_type}{path.suffix}"
                )

            filtered.save(output_path)

            return {
                "success": True,
                "input": image_path,
                "output": output_path,
                "filter": filter_type,
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


def create_thumbnail(
    image_path: str, max_size: int = 128, output_path: Optional[str] = None
) -> dict:
    """
    Create a thumbnail of an image.

    Args:
        image_path: Path to the input image
        max_size: Maximum size for width or height (default 128)
        output_path: Path to save thumbnail (optional)

    Returns:
        Dictionary with operation result
    """
    try:
        with Image.open(image_path) as img:
            img.thumbnail((max_size, max_size))

            if output_path is None:
                path = Path(image_path)
                output_path = str(path.parent / f"{path.stem}_thumb{path.suffix}")

            img.save(output_path)

            return {
                "success": True,
                "input": image_path,
                "output": output_path,
                "thumbnail_size": f"{img.width}x{img.height}",
            }
    except Exception as e:
        return {"success": False, "error": str(e)}
