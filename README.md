# Metallurgical Image Analysis for Grain Properties

## Project Goal

This project implements an automated image analysis pipeline in Python to identify and characterize the grains in metallographic microscope images. The primary objective is to process raw images and extract a comprehensive set of morphological and intensity-based properties for each individual grain.

This was developed as an enhancement of an original project for the EMS420 Module.

## Features Extracted

For each detected grain, the script calculates and saves the following properties:

* **Area:** The total number of pixels in the grain.
* **Perimeter:** The length of the grain's boundary.
* **Solidity:** The ratio of the grain's area to the area of its convex hull. A measure of how "solid" or "holey" the grain is.
* **Eccentricity:** A measure of how much the grain deviates from being a perfect circle (0 for a circle, 1 for a line).
* **Equivalent Diameter:** The diameter of a circle with the same area as the grain.
* **Orientation:** The angle of the grain's longest axis relative to the horizontal axis.
* **Major and Minor Axis Length:** The lengths of the principal axes of the ellipse that best fits the grain.

## Methodology

The project is structured into a modular and interactive workflow:

1.  **Utility Functions (`src/utils.py`):** Core image processing logic (segmentation, feature extraction, visualization) is separated into a "helper" file. This promotes code reusability and makes the main script easier to read.
2.  **Interactive Processor (`interactive_processor.py`):** This is the main script. It iterates through each raw image and enters an interactive loop that:
    * Prompts the user to input processing parameters (`sigma`, `block_size`, etc.).
    * Provides immediate visual feedback by displaying the resulting mask and opening an interactive plot in the browser.
    * Asks for user approval to ensure segmentation accuracy. If rejected, the user can re-enter new parameters for the same image.
3.  **Data Analysis Notebook (`Analysis.ipynb`):** After processing is complete, this Jupyter Notebook is used to load the generated data, perform comparative statistical analysis, and create final summary visualizations.

## How to Use
1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Add images:** Place your sample images into the correct subdirectories (e.g., `images/raw/X-6/`) - Must be JPGs.
3.  **Run the interactive processor:**
    ```bash
    python interactive_processor.py
    ```
4.  **Follow the prompts:**
    * In your terminal, enter the desired processing parameters for each image. Pressing `Enter` will accept the default value.
    * A window will pop up showing the generated mask. Review it and **press any key** to close it.
    * A new tab will open in your web browser with an interactive plot.
    * Return to your terminal and type `y` to approve and save the result, or `n` to reject and try again.
5.  **Find your results:**
    * **Data:** `.csv` files will be in `/data/<sample_type>/`.
    * **Final Plots:** `.png` and `.html` files will be in `/output/`.
6.  **Review the analysis:** Open and run the `Analysis.ipynb` Jupyter Notebook to see the detailed data analysis.


## Results

Here is an example of the pipeline's output, showing the original image and the final segmented mask.


![Example Comparison](output/comparison_images/X-6/X-6_1_comparison.png)`

## Technologies Used
- Python
- OpenCV
- Scikit-image
- Plotly
- Matplotlib
- Pandas
- Numpy
