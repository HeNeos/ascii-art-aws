from lambdas.proccess_frames.modules.ascii_dict import AsciiDict


def map_to_char(gray_scale: float, ascii_dict: AsciiDict) -> str:
    position: int = int(((len(ascii_dict.value) - 1) * gray_scale) / 255)
    return ascii_dict.value[position]


# def calculate_scale(
#     image_size: Tuple[int, int], scale: Optional[Union[int, float]] = None
# ) -> int:
#     if scale:
#         return int(scale)
#     max_length = 200
#     max_size = max(image_size)
#     new_scale: int = (max_size + max_length - 1) // max_length
#     return new_scale


# def cut_grid(grid: List[List[str]]) -> List[List[str]]:
#     resized_grid: List[List[str]] = []
#     for line in grid:
#         if not all(column == " " for column in line):
#             resized_grid.append(line)
#     return resized_grid
