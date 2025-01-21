import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import matplotlib.patches as patches
import mysql.connector
from PyPDF2 import PdfMerger
from mysql.connector import Error
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime
import os

# Singleton class for database connection
class DatabaseConnectionSingleton:
    _instance = None

    @classmethod
    def get_instance(cls, host, user, password, database):
        """
        Returns a singleton instance of the database connection.
        Reinitializes the connection if it is closed or stale.
        """
        if cls._instance is None:
            cls._instance = cls._initialize_connection(host, user, password, database)
        else:
            try:
                # Check if the connection is still active
                cls._instance.ping(reconnect=True)
            except Error as e:
                print(f"Reinitializing database connection due to error: {e}")
                cls._instance = cls._initialize_connection(host, user, password, database)
        return cls._instance

    @classmethod
    def _initialize_connection(cls, host, user, password, database):
        """
        Initializes a new database connection.
        """
        try:
            connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            print("Database connection initialized.")
            return connection
        except Error as e:
            print(f"Error initializing database connection: {e}")
            return None

    @classmethod
    def close_instance(cls):
        """
        Closes the database connection if it exists.
        """
        if cls._instance is not None:
            try:
                cls._instance.close()
                print("Database connection closed.")
            except Error as e:
                print(f"Error closing database connection: {e}")
            finally:
                cls._instance = None


# Data Processor Class
class DataProcessor:
    def __init__(self, connection):
        self.connection = connection

    def fetch_data(self, query):
        """
        Fetches data from the database using the provided query.
        """
        try:
            df = pd.read_sql(query, self.connection)
            print("Data fetched successfully.")
            return df
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None

    def create_pivot_table(self, df, values_column, index_column, columns_column):
        """
        Creates a pivot table from the DataFrame.
        """
        pivot_table = pd.pivot_table(
            df,
            values=values_column,
            index=index_column,
            columns=columns_column,
            aggfunc='count',
            fill_value=0
        )
        return pivot_table

    def plot_data(self, pivot_table, output_file="output_plot.pdf"):
        """
        Plots the data using the pivot table.
        """
        fig, axs = plt.subplots(2, 1, figsize=(12, 12))

        # Stacked bar plot
        pivot_table.plot(kind='bar', stacked=True, color=sns.color_palette("husl", len(pivot_table.columns)), ax=axs[0])
        axs[0].set_title('Count of Cases by Case Status and Gender', fontsize=15, weight='bold')
        axs[0].set_xlabel('Case Status', fontsize=14, labelpad=10)
        axs[0].set_ylabel('Number of Cases', fontsize=14, labelpad=10)
        axs[0].set_xticklabels(pivot_table.index, rotation=45, ha='right')
        axs[0].legend(title='Gender', fontsize=12)
        axs[0].grid(axis='y', linestyle='--', alpha=0.7)

        # Table
        axs[1].axis('off')
        table = axs[1].table(cellText=pivot_table.values,
                             rowLabels=pivot_table.index,
                             colLabels=pivot_table.columns,
                             loc='center')
        axs[1].set_title('Pivot Table of Cases by Status and Gender', fontsize=16, fontweight='bold')

        # Comments and styling
        fig.text(0.5, 0.000000099, 'Report analysis by Mediport', ha='center', va='center', fontsize=13, fontweight='bold')
        fig.text(0.5, 1.1000001, 'Vagus Hospital', ha='center', va='center', fontsize=20, fontweight='bold')
        border = patches.Rectangle((-0.03, -0.03), 1.17, 1.17, transform=fig.transFigure, color='black', linewidth=3, fill=False)
        fig.patches.append(border)
        plt.tight_layout()
        plt.savefig(output_file, bbox_inches='tight', pad_inches=0.5)
        ### 
        print(f'Both the stacked bar plot and pivot table have been saved as {output_file}')

    # Function to add diagonal watermark
    def add_diagonal_watermarks(self, fig, text, alpha=0.30, fontsize=30, rotation=30, spacing=0.25):
        for x in np.arange(0, 1 + spacing, spacing):
            for y in np.arange(0, 1 + spacing, spacing):
                fig.text(x, y, text, fontsize=fontsize, color='black',
                         ha='center', va='center', alpha=alpha, rotation=rotation)

    # free reports
    def report_with_watermark(self, df,Water_mark=True):
        # Ensure 'Age(Years)' column is numeric
        df['Age(Years)'] = pd.to_numeric(df['Age(Years)'], errors='coerce')

        # Drop rows where 'Age(Years)' is NaN after conversion
        df = df.dropna(subset=['Age(Years)'])

        # Grouping the data by 'Patient District' and counting the cases
        patient_district = 'Patient District'
        district_case_count = df.groupby(patient_district).size().reset_index(name='Case Count')

        # Calculate the percentage of cases for each district
        total_cases = district_case_count['Case Count'].sum()
        district_case_count['Percentage'] = (district_case_count['Case Count'] / total_cases) * 100

        # Seaborn theme for a cleaner look
        sns.set_theme(style="whitegrid")

        # Colors for the bars
        colors = sns.color_palette("viridis", len(district_case_count))

        # Define the Reports folder path
        reports_folder = os.path.join(os.getcwd(), "Reports")

        # Ensure the Reports folder exists
        os.makedirs(reports_folder, exist_ok=True)

        # Full path for the PDF file
        pdf_file_path = os.path.join(reports_folder, "charts_summary_with_watermark.pdf")

        # Create a PDF to save the final result
        with PdfPages(pdf_file_path) as pdf:
            # Create figure and GridSpec for a 2x2 layout
            fig = plt.figure(figsize=(14, 12))
            gs = plt.GridSpec(2, 2, wspace=0.4, hspace=0.6)

            # First plot: District Case Count (Horizontal Bar Plot)
            ax1 = fig.add_subplot(gs[0, 0])
            bars = ax1.barh(district_case_count[patient_district], district_case_count['Case Count'],
                            color=colors, edgecolor='black', label='Case Count')
            for bar, case_count, percentage in zip(bars, district_case_count['Case Count'],
                                                   district_case_count['Percentage']):
                width = bar.get_width()
                ax1.text(width + 0.05 * max(district_case_count['Case Count']), bar.get_y() + bar.get_height() / 2,
                         f'{case_count} ({percentage:.1f}%)', ha='left', va='center', fontsize=11, fontweight='bold')
            ax1.set_title('Cases by District with Case Count and Percentage', fontsize=14)
            ax1.set_xlabel('Case Count')
            ax1.set_ylabel('District')
            ax1.grid(True, axis='x', linestyle='--', alpha=0.7)

            # Second plot: Gender Case Distribution (Pie Chart)
            genderAll = 'Gender'
            gender_case_count = df.groupby(genderAll).size().reset_index(name='Case Count')
            ax2 = fig.add_subplot(gs[0, 1])
            ax2.pie(gender_case_count['Case Count'], labels=gender_case_count[genderAll], autopct='%1.1f%%',
                    startangle=140)
            ax2.set_title('Counts of Cases by Gender', fontsize=14)

            # Third plot: Death Counts by Age Group (Bar Chart)
            bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
            labels = ['0-10', '11-20', '21-30', '31-40', '41-50', '51-60', '61-70', '71-80', '81-90', '90-100']
            df['Age Group'] = pd.cut(df['Age(Years)'], bins=bins, labels=labels, right=False)

            death_df = df[df['Death Date'].notnull()]
            pivot_table = pd.pivot_table(death_df, index='Age Group', values='Case No', aggfunc='count', observed=False)

            ax3 = fig.add_subplot(gs[1, 0])
            ax3.bar(pivot_table.index, pivot_table['Case No'], color='lightblue', edgecolor='black')
            ax3.set_xlabel('Age Group')
            ax3.set_ylabel('Count')
            ax3.set_title('Count of Deaths by Age Group', fontsize=14)
            ax3.set_xticks(range(len(pivot_table.index)))  # Set fixed ticks
            ax3.set_xticklabels(pivot_table.index, rotation=45)

            # Fourth plot: Death Counts by Gender (Donut Chart)
            gender_death_count = death_df.groupby('Gender').size().reset_index(name='Death Count')
            total_deaths = gender_death_count['Death Count'].sum()
            labels = [f'{gender} - {count} deaths\n({count / total_deaths:.1%})'
                      for gender, count in zip(gender_death_count['Gender'], gender_death_count['Death Count'])]
            explode = np.where(gender_death_count['Death Count'] / total_deaths < 0.05, 0.2, 0)

            ax4 = fig.add_subplot(gs[1, 1], aspect='equal')
            wedges, texts, autotexts = ax4.pie(gender_death_count['Death Count'], wedgeprops=dict(width=0.4),
                                               startangle=140, explode=explode, pctdistance=0.75,
                                               autopct='%1.1f%%', colors=['#ff9999', '#66b3ff'])
            for autotext in autotexts:
                autotext.set_color('black')
                autotext.set_fontsize(10)
            for i, p in enumerate(wedges):
                ang = (p.theta2 - p.theta1) / 2. + p.theta1  # Compute angle for annotation
                x, y = np.cos(np.deg2rad(ang)), np.sin(np.deg2rad(ang))
                ax4.annotate(labels[i], xy=(x, y), xytext=(1.4 * np.sign(x), 1.4 * y),
                             horizontalalignment={-1: "right", 1: "left"}[int(np.sign(x))],
                             arrowprops=dict(arrowstyle="-", connectionstyle=f"angle,angleA=0,angleB={ang}"),
                             bbox=dict(boxstyle="round,pad=0.3", fc="w", ec="k", lw=0.72))
            ax4.set_title(f'Death Counts by Gender (Total: {total_deaths})', fontsize=14)
            # Add comments under each plot
            # fig.text(0.5, 0.96, 'Vagus Hospital', ha='center', va='center', fontsize=20, fontweight='bold')
            fig.text(0.1, 0.52, 'Cases by District provide a geographical view of the case  distribution.', ha='left',
                     va='center', fontsize=13)
            fig.text(0.6, 0.52, 'Gender-based distribution of cases highlights demographic insights.', ha='left',
                     va='center', fontsize=13)
            fig.text(0.1, 0.02, 'Deaths by Age Group showcase vulnerability across different age ranges.', ha='left',
                     va='center', fontsize=13)
            fig.text(0.6, 0.02, 'Gender-based death counts provide insights into mortality trends by gender.',
                     ha='left', va='center', fontsize=13)

            # Add comments under each plot
            fig.text(0.5, 0.0079, 'Report analysis by Mediport', ha='center', va='center', fontsize=13,
                     fontweight='bold')
            fig.text(0.5, 1.009941, 'Vagus Hospital', ha='center', va='center', fontsize=20, fontweight='bold')
            # Add a full-page bold border
            border = patches.Rectangle((-0.08, -0.08), 1.17, 1.17, transform=fig.transFigure, color='black',
                                       linewidth=3, fill=False)
            fig.patches.append(border)

            # Add diagonal watermarks
            if Water_mark == True:
                text = 'MEDIPORT'
                self.add_diagonal_watermarks(plt.gcf(), text, alpha=0.55, fontsize=30, rotation=30, spacing=0.25)

            # Save the figure into the PDF
            pdf.savefig(fig, bbox_inches='tight')

        print(f"Report saved successfully at: {pdf_file_path}")
        return pdf_file_path

    def plot_death_case_distribution(self, df,Water_mark=True):
        # Convert 'Age(Years)' to numeric, coercing errors to NaN
        df['Age(Years)'] = pd.to_numeric(df['Age(Years)'], errors='coerce')

        # Handle missing values (e.g., replace NaN with 0 or drop rows with NaN)
        df['Age(Years)'] = df['Age(Years)'].fillna(0)  # Replace NaN with 0

        # Define bins for age groups
        bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        labels = ['0-10', '11-20', '21-30', '31-40', '41-50', '51-60', '61-70', '71-80', '81-90', '91-100']

        # Categorize ages into age groups
        df['Age Group'] = pd.cut(df['Age(Years)'], bins=bins, labels=labels, right=False)

        # Filter the DataFrame for records with a death date
        death_df = df[df['Death Date'].notnull()]

        # Create a pivot table to count deaths by age group
        pivot_table = pd.pivot_table(death_df, index='Age Group', values='Case No', aggfunc='count')

        # Create a new figure to combine the plots
        fig, axs = plt.subplots(2, 1, figsize=(14, 12))

        # Plot 1: Stacked Bar Chart for Case Type Distribution by Age Group
        if 'Case Type' in df.columns:
            # Create a pivot table for case type counts
            case_type_counts = pd.pivot_table(df, values='Case No', index='Age Group', columns='Case Type',
                                              aggfunc='count', fill_value=0)
            case_type_counts.plot(kind='bar', stacked=True, ax=axs[0], color=plt.cm.Paired.colors)

            axs[0].set_title('Case Type Distribution by Age Group', fontsize=14, fontweight='bold')
            axs[0].set_ylabel('Number of Cases')
            axs[0].tick_params(axis='x', rotation=45)

        # Plot 2: Count of Deaths by Age Group
        specific_colors = ['red', 'blue', 'green', 'yellow', 'orange', 'purple', 'cyan', 'magenta', 'gray', 'brown']
        bars = axs[1].bar(pivot_table.index, pivot_table['Case No'], color=specific_colors[:len(pivot_table.index)])
        axs[1].set_xlabel('Age Group')
        axs[1].set_ylabel('Count')
        axs[1].set_title('Count of Deaths by Age Group', fontsize=16, fontweight='bold')
        axs[1].tick_params(axis='x', rotation=45)

        # Adding the count on top of each bar for better visibility
        for bar in bars:
            yval = bar.get_height()
            axs[1].text(bar.get_x() + bar.get_width() / 2, yval, int(yval), ha='center', va='bottom', fontsize=10)
        if Water_mark == True:
            # Add diagonal watermarks across the entire page
            self.add_diagonal_watermarks(fig, 'MEDIPORT', alpha=0.30, fontsize=30, rotation=30, spacing=0.25)

        # Add comments about the plots
        fig.text(0.5, 1.02, 'Report Analysis By Mediport', ha='center', fontsize=20, fontweight='bold')
        fig.text(0.5, 0.5,
                 'The first plot shows the distribution of case types across different age groups, while the second plot depicts the count of deaths by age group.',
                 ha='center', fontsize=12)
        fig.text(0.5, 0.02, 'The analysis provides insights into age demographics and case type prevalence.',
                 ha='center', fontsize=12)

        # Add a border around the entire figure
        border = patches.Rectangle(
            (-0.05, -0.05), 1.1, 1.1,
            transform=fig.transFigure, color='black', linewidth=3, fill=False
        )
        fig.patches.append(border)

        # Adjust layout to prevent overlap
        plt.tight_layout()

        # Ensure the Reports folder exists
        reports_folder = os.path.join(os.getcwd(), "Reports")
        os.makedirs(reports_folder, exist_ok=True)

        # Save the combined plots as a PDF
        combined_pdf_path = os.path.join(reports_folder, "combined_death_case_distribution.pdf")
        plt.savefig(combined_pdf_path, format='pdf', bbox_inches='tight', pad_inches=0.5)
        plt.close(fig)

        print(f'Combined plots saved as {combined_pdf_path}')
        return combined_pdf_path

    def save_combined_pivot_tables_as_pdf(self,df, index_column, columns_column, values_column, Water_mark=True):
        """
        Creates two pivot tables and saves them as a single PDF with comments and watermarks.

        Parameters:
        df (pd.DataFrame): The input DataFrame containing case data.
        index_column (str): The column name to use as the index in the first pivot table.
        columns_column (str): The column name to use as the columns in the first pivot table.
        values_column (str): The column name to use for values in the first pivot table.
        """

        # Create the first pivot table
        pivot_table1 = pd.pivot_table(
            df,
            values=values_column,
            index=index_column,
            columns=columns_column,
            aggfunc='count',
            fill_value=0
        )

        # Create the second pivot table
        pivot_table2 = pd.pivot_table(
            df,
            values='Claim Initaiated Amount(Rs.)',
            index='Case Status',
            aggfunc='sum',
            margins=True,
            margins_name='Total Grand'
        )

        # Create a figure with two subplots
        fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(10, 12))

        # First subplot for the first pivot table
        axes[0].axis('off')
        axes[0].table(cellText=pivot_table1.values,
                      rowLabels=pivot_table1.index,
                      colLabels=pivot_table1.columns,
                      loc='center')
        axes[0].set_title('Analysis: Case Status by Gender', fontsize=16, fontweight='bold')

        # Second subplot for the second pivot table
        axes[1].axis('off')
        axes[1].table(cellText=pivot_table2.values,
                      rowLabels=pivot_table2.index,
                      colLabels=pivot_table2.columns,
                      loc='center')
        axes[1].set_title('Case Status Claim Amounts', fontsize=16, fontweight='bold')
        if Water_mark == True:
            # Add diagonal watermarks across the entire page
            self.add_diagonal_watermarks(plt.gcf(), 'MEDIPORT', alpha=0.30, fontsize=30, rotation=30, spacing=0.25)

        # Add comments under each plot
        fig.text(0.5, 0.99999, 'Vagus Hospital', ha='center', va='center', fontsize=20, fontweight='bold')
        fig.text(0.1, 0.5, 'Case Status by Gender Count', ha='left', va='center', fontsize=13)
        fig.text(0.1, 0.02, 'Case Status Claim Amounts', ha='left', va='center', fontsize=13)
        fig.text(0.5, 0.00099, 'Report analysis by Mediport', ha='center', va='center', fontsize=20, fontweight='bold')

        # Add a border around the entire figure
        border = patches.Rectangle((-0.099, -0.099), 1.20, 1.20, transform=fig.transFigure, color='black', linewidth=3,
                                   fill=False)
        fig.patches.append(border)

        # Ensure the Reports folder exists
        reports_folder = os.path.join(os.getcwd(), "Reports")
        if not os.path.exists(reports_folder):
            os.makedirs(reports_folder)

        # Save the figure as a PDF
        pdf_file_path = os.path.join(reports_folder, "combined_pivot_table_report.pdf")
        plt.tight_layout()
        plt.savefig(pdf_file_path, format='pdf', bbox_inches='tight', pad_inches=0.5)
        #    # Close the plot to avoid displaying it

        print(f'Combined pivot tables saved as {pdf_file_path}')
        return pdf_file_path

    def combine_pdfs(self, pdf_files, output_dir="Reports"):
        """
        Combines multiple PDF files into a single PDF.
        Generates a unique name for the combined file and avoids overwriting.
        """
        try:
            merger = PdfMerger()
            valid_files = []

            # Validate and append PDFs
            for pdf in pdf_files:
                if os.path.exists(pdf):
                    try:
                        merger.append(pdf)
                        valid_files.append(pdf)  # Track valid files for deletion
                    except Exception as e:
                        print(f"Error appending {pdf}: {e}")
                else:
                    print(f"File not found: {pdf}")

            # Write the combined PDF
            if valid_files:
                # Generate a unique output file name
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = os.path.join(output_dir,f"Combined_Reports{timestamp}.pdf")
                os.makedirs(output_dir, exist_ok=True)

                # Write the combined PDF
                merger.write(output_file)
                merger.close()
                print(f"All PDFs have been combined into {output_file}.")

                # Return the path to the combined PDF
                return output_file
            else:
                print("No valid PDF files to combine.")
                return None

        except Exception as e:
            print(f"Error combining PDFs: {e}")
            return None

    #paid reports
    def count_of_case_status(self,df):
        # Step 1: Create the pivot table
        pivot_table = pd.pivot_table(
            df,
            values='Case No',  # Use 'Case No' to count the number of cases
            index='Case Status',
            columns='Gender',
            aggfunc='count',
            fill_value=0
        )

        # Step 2: Create a figure with subplots
        fig, axs = plt.subplots(2, 1, figsize=(12, 12))  # Two rows, one column

        # Step 3: Create a stacked bar plot
        pivot_table.plot(kind='bar', stacked=True, color=sns.color_palette("husl", len(pivot_table.columns)), ax=axs[0])

        # Step 4: Add titles and labels for the bar plot
        axs[0].set_title('Count of Cases by Case Status and Gender', fontsize=15, weight='bold')
        axs[0].set_xlabel('Case Status', fontsize=14, labelpad=10)
        axs[0].set_ylabel('Number of Cases', fontsize=14, labelpad=10)
        axs[0].set_xticklabels(pivot_table.index, rotation=45,
                               ha='right')  # Rotate x-axis labels for better readability
        axs[0].legend(title='Gender', fontsize=12)  # Add legend for Gender

        # Step 5: Add grid lines for better clarity
        axs[0].grid(axis='y', linestyle='--', alpha=0.7)

        # Step 6: Create a table for the pivot table in the second subplot
        axs[1].axis('off')  # Hide the axis for the pivot table

        # Create a table from the pivot table
        table = axs[1].table(cellText=pivot_table.values,
                             rowLabels=pivot_table.index,
                             colLabels=pivot_table.columns,
                             loc='center')

        # Add a title to the table
        axs[1].set_title('Pivot Table of Cases by Status and Gender', fontsize=16, fontweight='bold')

        # Add comments to explain the plot
        comment_plot = "This plot shows the count of cases by status for each gender. Each color represents a different gender."
        plt.text(0.5, -0.75, comment_plot, ha='center', va='center', fontsize=12, transform=axs[0].transAxes)

        comment_table = "This table shows the count of cases by status for each gender. The first table represents the case status, and the second and third represent the gender."
        plt.text(0.5, -0.09, comment_table, ha='center', va='center', fontsize=12, transform=axs[1].transAxes)

        # Add comments under each plot
        fig.text(0.5, 0.000000099, 'Report analysis by Mediport', ha='center', va='center', fontsize=13,
                 fontweight='bold')
        fig.text(0.5, 1.1000001, 'Vagus Hospital', ha='center', va='center', fontsize=20, fontweight='bold')

        # Step 7: Add a border around the entire figure
        border = patches.Rectangle((-0.03, -0.03), 1.17, 1.17, transform=fig.transFigure, color='black', linewidth=3,
                                   fill=False)
        fig.patches.append(border)

        # Adjust layout
        plt.tight_layout()

        # Ensure the Reports folder exists
        reports_folder = os.path.join(os.getcwd(), "Reports")
        if not os.path.exists(reports_folder):
            os.makedirs(reports_folder)

        # Save the combined figure as a PDF in the Reports folder
        pdf_file_path = os.path.join(reports_folder, "combined_counts_and_pivot_table.pdf")
        plt.savefig(pdf_file_path, bbox_inches='tight', pad_inches=0.5)
        ##   # Show the plot

        print(f'Report saved successfully at: {pdf_file_path}')
        return pdf_file_path

    def death_by_gender(self,df):
        # Group by Gender where Death Date is not null and count occurrences
        gender_death_count = df[df['Death Date'].notnull()].groupby('Gender').size().reset_index(name='Death Count')

        # Calculate the total death count
        total_deaths = gender_death_count['Death Count'].sum()

        # Prepare labels with gender and death counts
        labels = [f'{gender} - {count} deaths\n({count / total_deaths:.1%})'
                  for gender, count in zip(gender_death_count['Gender'], gender_death_count['Death Count'])]

        # Explode the slices for better visibility (optional)
        explode = np.where(gender_death_count['Death Count'] / total_deaths < 0.05, 0.2, 0)

        # Set up the figure and axes
        fig, axs = plt.subplots(2, 1, figsize=(10, 12), gridspec_kw={'height_ratios': [3, 1]})  # Two rows, one column

        # Plotting the donut chart (pie chart with a hole in the center)
        wedges, texts, autotexts = axs[0].pie(gender_death_count['Death Count'],
                                              wedgeprops=dict(width=0.4),  # Donut chart style
                                              startangle=140,
                                              explode=explode,
                                              pctdistance=0.75,
                                              autopct='%1.1f%%',  # Adding percentage on each slice
                                              colors=['#ff9999', '#66b3ff'])

        # Formatting the percentage text
        for autotext in autotexts:
            autotext.set_color('black')
            autotext.set_fontsize(10)

        # Adding annotations with gender, death counts, and percentages
        bbox_props = dict(boxstyle="round,pad=0.3", fc="w", ec="k", lw=0.72)
        kw = dict(arrowprops=dict(arrowstyle="-"), bbox=bbox_props, zorder=0, va="center")

        for i, p in enumerate(wedges):
            ang = (p.theta2 - p.theta1) / 2. + p.theta1
            y = np.sin(np.deg2rad(ang))
            x = np.cos(np.deg2rad(ang))
            horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
            connectionstyle = f"angle,angleA=0,angleB={ang}"
            kw["arrowprops"].update({"connectionstyle": connectionstyle})
            axs[0].annotate(labels[i], xy=(x, y), xytext=(1.4 * np.sign(x), 1.4 * y),
                            horizontalalignment=horizontalalignment, **kw)

        # Adding a title with the total death count
        axs[0].set_title(f'Death Counts by Gender (Total: {total_deaths})', fontsize=16, fontweight='bold')

        # Draw a circle in the center for the donut effect
        centre_circle = plt.Circle((0, 0), 0.35, fc='white')
        axs[0].add_artist(centre_circle)

        # Hide the axis for the second subplot
        axs[1].axis('off')

        # Create a table for the death count data in the second subplot
        table = axs[1].table(cellText=gender_death_count.values,
                             colLabels=gender_death_count.columns,
                             loc='center')

        # Add comments to explain the plot
        comment_plot = "This plot shows the count of Death by gender. Each color represents a different gender."
        plt.text(0.5, 0.009, comment_plot, ha='center', va='center', fontsize=12, transform=axs[0].transAxes)

        comment_table = "This table shows the 'Count Of Death' by each gender. The first table represents the Gender and the second table represents Death Counts."
        plt.text(0.5, -0.09, comment_table, ha='center', va='center', fontsize=12, transform=axs[1].transAxes)

        # Add comments under each plot
        fig.text(0.5, -0.019001199, 'Report analysis by Mediport', ha='center', va='center', fontsize=13,
                 fontweight='bold')
        fig.text(0.5, 1.0089001, 'Vagus Hospital', ha='center', va='center', fontsize=20, fontweight='bold')

        # Step 7: Add a border around the entire figure
        border = patches.Rectangle((-0.059, -0.059), 1.17, 1.17, transform=fig.transFigure, color='black', linewidth=3,
                                   fill=False)
        fig.patches.append(border)

        # Adjust layout
        plt.tight_layout()

        # Ensure the Reports folder exists
        reports_folder = os.path.join(os.getcwd(), "Reports")
        if not os.path.exists(reports_folder):
            os.makedirs(reports_folder)

        # Save the combined figure as a PDF in the Reports folder
        pdf_file_path = os.path.join(reports_folder, "death_counts_by_gender_and_table.pdf")
        plt.savefig(pdf_file_path, bbox_inches='tight', pad_inches=0.5)
        ##   # Show the plot

        print(f'Report saved successfully at: {pdf_file_path}')
        return pdf_file_path

    def death_by_age(self,df):
        # Define age group bins and labels
        bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        labels = ['0-10', '11-20', '21-30', '31-40', '41-50', '51-60', '61-70', '71-80', '81-90', '91-100']

        # Create a new column 'Age Group' based on the age ranges
        df['Age Group'] = pd.cut(df['Age(Years)'], bins=bins, labels=labels, right=False)

        # Filter the dataframe to include only rows where 'Death Date' is not null
        death_df = df[df['Death Date'].notnull()]

        # Create a pivot table to show the count of deaths by age group
        pivot_table = pd.pivot_table(death_df, index='Age Group', values='Case No', aggfunc='count')

        # Set up the figure and axes
        fig, axs = plt.subplots(2, 1, figsize=(10, 12), gridspec_kw={'height_ratios': [3, 1]})

        # Create a bar chart for the count of deaths by age group
        bars = axs[0].bar(pivot_table.index, pivot_table['Case No'], color='skyblue')
        axs[0].set_xlabel('Age Group', fontsize=14, labelpad=10)
        axs[0].set_ylabel('Count', fontsize=14, labelpad=10)
        axs[0].set_title('Count of Deaths by Age Group', fontsize=14, fontweight='bold')
        axs[0].set_xticklabels(pivot_table.index, rotation=45, ha='right')

        # Add case count on top of each bar
        for bar in bars:
            yval = bar.get_height()
            axs[0].text(bar.get_x() + bar.get_width() / 2, yval + 0.1, int(yval), ha='center', va='bottom', fontsize=12)

        # Hide the axis for the second subplot
        axs[1].axis('off')

        # Create a table for the death count data in the second subplot
        table = axs[1].table(cellText=pivot_table.values,
                             colLabels=pivot_table.columns,
                             rowLabels=pivot_table.index,
                             loc='center')

        # Add comments to explain the plot
        comment_plot = "This plot shows the count of deaths by age group."
        axs[0].text(0.5, -0.14, comment_plot, ha='center', va='center', fontsize=12, transform=axs[0].transAxes)

        comment_table = "This table shows the count of deaths by each age group."
        axs[1].text(0.5, -0.09, comment_table, ha='center', va='center', fontsize=12, transform=axs[1].transAxes)

        # Add comments under each plot
        fig.text(0.5, -0.019001199, 'Report analysis by Mediport', ha='center', va='center', fontsize=13,
                 fontweight='bold')
        fig.text(0.5, 1.0189001, 'Vagus Hospital', ha='center', va='center', fontsize=20, fontweight='bold')

        # Add a border around the entire figure
        border = patches.Rectangle((-0.059, -0.059), 1.17, 1.17, transform=fig.transFigure, color='black', linewidth=3,
                                   fill=False)
        fig.patches.append(border)

        # Adjust layout
        plt.tight_layout()

        # Ensure the Reports folder exists
        reports_folder = os.path.join(os.getcwd(), "Reports")
        if not os.path.exists(reports_folder):
            os.makedirs(reports_folder)

        # Save the combined figure as a single PDF file in the Reports folder
        pdf_file_path = os.path.join(reports_folder, "age_group_death_count_and_table.pdf")
        plt.savefig(pdf_file_path, bbox_inches='tight', pad_inches=0.5)
        ## 

        print(f'Report saved successfully at: {pdf_file_path}')
        return pdf_file_path

    def count_cases_by_age(self, df):
        # Convert 'Age(Years)' to numeric, coercing errors to NaN
        df['Age(Years)'] = pd.to_numeric(df['Age(Years)'], errors='coerce')

        # Handle missing values (e.g., replace NaN with 0 or drop rows with NaN)
        df['Age(Years)'] = df['Age(Years)'].fillna(0)  # Replace NaN with 0

        # Define age group bins and labels
        bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        labels = ['0-10', '11-20', '21-30', '31-40', '41-50', '51-60', '61-70', '71-80', '81-90', '91-100']

        # Create a new column 'Age Group' based on the age ranges
        df['Age Group'] = pd.cut(df['Age(Years)'], bins=bins, labels=labels, right=False)

        # Create a pivot table to show the count of cases by age group
        pivot_table = pd.pivot_table(df, index='Age Group', values='Case No', aggfunc='count')

        # Set up the figure with two subplots for the bar plot and table
        fig, axs = plt.subplots(2, 1, figsize=(10, 12), gridspec_kw={'height_ratios': [2, 1]})

        # Plot the bar chart
        bars = axs[0].bar(pivot_table.index, pivot_table['Case No'], color='skyblue')
        axs[0].set_xlabel('Age Group', fontsize=14)
        axs[0].set_ylabel('Count of Cases', fontsize=14)
        axs[0].set_title('Count of Cases by Age Group', fontsize=16, fontweight='bold')
        axs[0].tick_params(axis='x', rotation=45)

        # Add counts on top of each bar
        for bar in bars:
            yval = bar.get_height()
            axs[0].text(bar.get_x() + bar.get_width() / 2, yval + 0.1, int(yval), ha='center', va='bottom', fontsize=12)

        # Hide the axis for the second subplot (table)
        axs[1].axis('off')

        # Display the table below the bar chart
        axs[1].table(cellText=pivot_table.values,
                     rowLabels=pivot_table.index,
                     colLabels=pivot_table.columns,
                     loc='center')

        # Add comments to explain the plot and table
        comment_plot = "This plot shows the count of cases by age group. Each bar represents the number of cases within a specific age range."
        axs[0].text(0.5, -0.15, comment_plot, ha='center', va='center', fontsize=12, transform=axs[0].transAxes)

        comment_table = "This table shows the 'Count of Cases' by each age group."
        axs[1].text(0.5, -0.09, comment_table, ha='center', va='center', fontsize=12, transform=axs[1].transAxes)

        # Add a title and footer to the entire figure
        fig.text(0.5, 1.02, 'Vagus Hospital', ha='center', va='center', fontsize=20, fontweight='bold')
        fig.text(0.5, -0.02, 'Report analysis by Mediport', ha='center', va='center', fontsize=13, fontweight='bold')

        # Add a border around the entire figure
        border = patches.Rectangle((-0.059, -0.059), 1.17, 1.17, transform=fig.transFigure, color='black', linewidth=3,
                                   fill=False)
        fig.patches.append(border)

        # Adjust layout
        plt.tight_layout()

        # Ensure the Reports folder exists
        reports_folder = os.path.join(os.getcwd(), "Reports")
        if not os.path.exists(reports_folder):
            os.makedirs(reports_folder)

        # Save the combined figure as a PDF file in the Reports folder
        pdf_file_path = os.path.join(reports_folder, "age_group_cases_bar_table.pdf")
        plt.savefig(pdf_file_path, bbox_inches='tight', pad_inches=0.5)
        ## 

        print(f'Report saved successfully at: {pdf_file_path}')
        return pdf_file_path

    def count_case_gender(self,df):
        # Define column name for gender
        genderAll = 'Gender'

        # Count cases by gender
        gender_case_count = df.groupby(genderAll).size().reset_index(name='Case Count')

        # Set up the figure and grid layout
        fig, axs = plt.subplots(2, 1, figsize=(10, 12), gridspec_kw={'height_ratios': [3, 1]})

        # Plot the pie chart in the first subplot
        axs[0].pie(gender_case_count['Case Count'],
                   labels=gender_case_count[genderAll],
                   autopct='%1.1f%%',
                   startangle=140)
        axs[0].set_title('Counts of Cases by Gender', fontsize=13, fontweight='bold')

        # Display the table in the second subplot
        axs[1].axis('off')
        table = axs[1].table(cellText=gender_case_count.values,
                             colLabels=gender_case_count.columns,
                             cellLoc='center',
                             loc='center')
        table.scale(1, 2)  # Adjust table size if needed

        # Add descriptive comments for the plot and table
        comment_plot = "This pie chart shows the distribution of cases by gender. Each color represents a different gender."
        fig.text(0.5, 0.3, comment_plot, ha='center', va='center', fontsize=12)

        comment_table = "The table below details the count of cases by gender, listing the gender category and case count."
        fig.text(0.5, 0.2, comment_table, ha='center', va='center', fontsize=12)

        # Add the title and footer to the entire figure
        fig.text(0.5, 1.0079001, 'Vagus Hospital', ha='center', va='center', fontsize=20, fontweight='bold')
        fig.text(0.5, 0.01, 'Report analysis by Mediport', ha='center', va='center', fontsize=13, fontweight='bold')

        # Draw a border around the entire figure
        border = patches.Rectangle((-0.059, -0.059), 1.17, 1.17, transform=fig.transFigure, color='black', linewidth=3,
                                   fill=False)
        fig.patches.append(border)

        # Adjust layout
        plt.tight_layout()

        # Ensure the Reports folder exists
        reports_folder = os.path.join(os.getcwd(), "Reports")
        if not os.path.exists(reports_folder):
            os.makedirs(reports_folder)

        # Save the figure as a PDF in the Reports folder
        pdf_file_path = os.path.join(reports_folder, "Gender_and_Table.pdf")
        fig.savefig(pdf_file_path, bbox_inches='tight', pad_inches=0.5, format='pdf')
        ## 

        print(f'Report saved successfully at: {pdf_file_path}')
        return pdf_file_path


    def casecount_by_casetype(self,df):
        # Define column name for Case Type
        CaseType = 'Case Type'

        # Group the data by 'Case Type' and count the cases
        case_type_count = df.groupby(CaseType).size().reset_index(name='Case Count')

        # Calculate the total number of cases
        total_cases = case_type_count['Case Count'].sum()

        # Prepare labels with case type, case counts, and percentages
        labels = [f'{case_type} - {count} cases\n({count / total_cases:.1%})'
                  for case_type, count in zip(case_type_count[CaseType], case_type_count['Case Count'])]

        # Explode the slices with fewer cases for better visibility
        explode = np.where(case_type_count['Case Count'] / total_cases < 0.05, 0.2, 0)

        # Set up the figure and grid layout
        fig, axs = plt.subplots(2, 1, figsize=(10, 12), gridspec_kw={'height_ratios': [3, 1]})

        # Plot the donut chart in the first subplot
        wedges, texts, autotexts = axs[0].pie(case_type_count['Case Count'],
                                              labels=None,  # Use custom labels instead
                                              wedgeprops=dict(width=0.4),
                                              startangle=180,
                                              explode=explode,
                                              pctdistance=0.55,
                                              autopct='%1.1f%%')

        # Set font size and color for percentage text inside wedges
        for autotext in autotexts:
            autotext.set_color('black')
            autotext.set_fontsize(10)

        # Add annotations with case types, counts, and percentages
        bbox_props = dict(boxstyle="round,pad=0.2", fc="w", ec="k", lw=0.72)
        kw = dict(arrowprops=dict(arrowstyle="-"), bbox=bbox_props, zorder=0, va="center")

        for i, p in enumerate(wedges):
            ang = (p.theta2 - p.theta1) / 2. + p.theta1
            y = np.sin(np.deg2rad(ang))
            x = np.cos(np.deg2rad(ang))
            horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
            connectionstyle = f"angle,angleA=0,angleB={ang}"
            kw["arrowprops"].update({"connectionstyle": connectionstyle})
            axs[0].annotate(labels[i], xy=(x, y), xytext=(1.35 * np.sign(x), 1.4 * y),
                            horizontalalignment=horizontalalignment, **kw)

        # Add title to the donut chart
        axs[0].set_title(f'Distribution of Cases by Case Type (Total: {total_cases})', fontsize=16, fontweight='bold')

        # Draw a white circle in the center for the donut effect
        centre_circle = plt.Circle((0, 0), 0.35, fc='white')
        axs[0].add_artist(centre_circle)

        # Display the table in the second subplot
        axs[1].axis('off')
        table = axs[1].table(cellText=case_type_count.values,
                             colLabels=case_type_count.columns,
                             cellLoc='center',
                             loc='center')
        table.scale(1, 2)  # Adjust table size if needed

        # Add descriptive comments below the chart and table
        comment_plot = "This donut chart shows the distribution of cases by case type. Each section represents a different case type."
        fig.text(0.5, 0.3, comment_plot, ha='center', va='center', fontsize=12)

        comment_table = "The table below details the count of cases by type, listing the case category and case count."
        fig.text(0.5, 0.2, comment_table, ha='center', va='center', fontsize=12)

        # Add the title and footer to the entire figure
        fig.text(0.5, 1.02, 'Vagus Hospital', ha='center', va='center', fontsize=20, fontweight='bold')
        fig.text(0.5, 0.01, 'Report analysis by Mediport', ha='center', va='center', fontsize=13, fontweight='bold')

        # Draw a border around the entire figure
        border = patches.Rectangle((-0.059, -0.059), 1.17, 1.17, transform=fig.transFigure, color='black', linewidth=3,
                                   fill=False)
        fig.patches.append(border)

        # Adjust layout
        plt.tight_layout()

        # Ensure the Reports folder exists
        reports_folder = os.path.join(os.getcwd(), "Reports")
        if not os.path.exists(reports_folder):
            os.makedirs(reports_folder)

        # Save the figure as a PDF in the Reports folder
        pdf_file_path = os.path.join(reports_folder, "Case_Type_Distribution_and_Table.pdf")
        fig.savefig(pdf_file_path, bbox_inches='tight', pad_inches=0.5, format='pdf')
        ## 

        print(f'Report saved successfully at: {pdf_file_path}')
        return pdf_file_path


    def casecount_by_location(self,df):
        # Define column name for Patient District
        patient_district = 'Patient District'

        # Group the data by 'Patient District' and count the cases
        district_case_count = df.groupby(patient_district).size().reset_index(name='Case Count')

        # Create a new figure for the combined plot and table
        combined_fig = plt.figure(figsize=(14, 12))

        # Create the horizontal bar plot in the first subplot
        ax_plot = combined_fig.add_subplot(211)  # First subplot for the bar plot
        bars = ax_plot.barh(district_case_count[patient_district], district_case_count['Case Count'],
                            color=sns.color_palette("viridis", len(district_case_count)), edgecolor='black')

        # Adding case count labels to the right of the bars
        for bar in bars:
            width = bar.get_width()
            ax_plot.text(width + 0.05 * max(district_case_count['Case Count']), bar.get_y() + bar.get_height() / 2,
                         f'{int(width)}', ha='left', va='center', fontsize=11, fontweight='bold')

        # Adding title and axis labels
        ax_plot.set_title(f'Cases by {patient_district}', fontsize=13, weight='bold', pad=20, color='#333333')
        ax_plot.set_ylabel('District', fontsize=14, labelpad=10)
        ax_plot.set_xlabel('Case Count', fontsize=14, labelpad=10)
        plt.yticks(fontsize=12)

        # Improve grid and background styling for clarity
        ax_plot.grid(True, axis='x', linestyle='--', alpha=0.7)
        ax_plot.spines['top'].set_visible(False)  # Removing the top spine for a cleaner look
        ax_plot.spines['right'].set_visible(False)  # Removing the right spine for a cleaner look

        # Create the table in the second subplot
        ax_table = combined_fig.add_subplot(212)  # Second subplot for the table
        ax_table.axis('off')  # Hide the axes for the table

        # Display the table without percentage
        table = ax_table.table(cellText=district_case_count.values,
                               colLabels=district_case_count.columns,
                               cellLoc='center', loc='center')
        table.scale(1, 2)  # Adjust table size for better readability

        # Add descriptive comments for the plot and table
        comment_plot = "This bar chart shows the distribution of cases by patient district. Each bar represents the number of cases from a specific district."
        combined_fig.text(0.5, 0.48, comment_plot, ha='center', va='center', fontsize=12)

        comment_table = "The table below details the count of cases by district, listing each district and the corresponding case count."
        combined_fig.text(0.5, 0.03, comment_table, ha='center', va='center', fontsize=12)

        # Add the title and footer to the entire figure
        combined_fig.text(0.5, 1.02, 'Vagus Hospital', ha='center', va='center', fontsize=20, fontweight='bold')
        combined_fig.text(0.5, 0.005, 'Report analysis by Mediport', ha='center', va='center', fontsize=13,
                          fontweight='bold')

        # Draw a border around the entire figure
        border = patches.Rectangle((-0.059, -0.059), 1.17, 1.17, transform=combined_fig.transFigure, color='black',
                                   linewidth=3, fill=False)
        combined_fig.patches.append(border)

        # Adjust layout to prevent overlap
        combined_fig.tight_layout()

        # Ensure the Reports folder exists
        reports_folder = os.path.join(os.getcwd(), "Reports")
        if not os.path.exists(reports_folder):
            os.makedirs(reports_folder)

        # Save the combined figure as a PDF in the Reports folder
        pdf_file_path = os.path.join(reports_folder, "District_Cases_Combined.pdf")
        combined_fig.savefig(pdf_file_path, bbox_inches='tight', pad_inches=0.5, format='pdf')
        print(f'Report saved successfully at: {pdf_file_path}')
        return pdf_file_path

    def casestatus_claim_amount_yearwise(self, df):
        # Convert 'Claim Submitted Date' to datetime
        df['Claim Submitted Date'] = pd.to_datetime(df['Claim Submitted Date'], errors='coerce')

        # Extract the year from 'Claim Submitted Date'
        df['Year'] = df['Claim Submitted Date'].dt.year

        # Filter the data for years 2022, 2023, and 2024
        df_filtered = df[df['Year'].isin([2022, 2023, 2024])]

        # Ensure numeric conversion for 'Claim Initaiated Amount(Rs.)'
        df['Claim Initaiated Amount(Rs.)'] = pd.to_numeric(df['Claim Initaiated Amount(Rs.)'], errors='coerce')

        # Create a pivot table for filtered data with 'Case Status' as rows and years as columns
        pivot_table_filtered = pd.pivot_table(
            df_filtered,
            values='Claim Initaiated Amount(Rs.)',
            index='Case Status',
            columns='Year',
            aggfunc='sum',
            fill_value=0,
            margins=True,
            margins_name='Grand Total'
        )

        # Create a pivot table for all data with 'Case Status' as rows
        pivot_table_all = pd.pivot_table(
            df,
            values='Claim Initaiated Amount(Rs.)',
            index='Case Status',
            aggfunc='sum',
            margins=True,
            margins_name='Total Grand'
        )

        # Ensure the Reports folder exists
        reports_folder = os.path.join(os.getcwd(), "Reports")
        os.makedirs(reports_folder, exist_ok=True)

        pdf_file_path = os.path.join(reports_folder, "case_status_claim_amt_combined.pdf")

        with PdfPages(pdf_file_path) as pdf:
            # Create a figure with subplots for both tables
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))

            # Hide the axes for both tables
            ax1.axis('off')
            ax2.axis('off')

            # Create a table from the filtered pivot table
            table_filtered = ax1.table(
                cellText=pivot_table_filtered.values,
                rowLabels=pivot_table_filtered.index,
                colLabels=pivot_table_filtered.columns,
                loc='center'
            )
            ax1.set_title('Case Status Claim Amt (Filtered)', fontsize=13, fontweight='bold')

            # Create a table from the all-data pivot table
            table_all = ax2.table(
                cellText=pivot_table_all.values,
                rowLabels=pivot_table_all.index,
                colLabels=pivot_table_all.columns,
                loc='center'
            )
            ax2.set_title('Case Status Claim Amt (All Data)', fontsize=13, fontweight='bold')

            # Add descriptive comments below the chart and table
            comment_plot = "This chart shows the distribution of cases by case type, with each color representing a different case category."
            fig.text(0.5, 0.58, comment_plot, ha='center', fontsize=12, fontstyle='italic')

            comment_table = "The table below provides a detailed summary of amounts related to each case status."
            fig.text(0.5, 0.01, comment_table, ha='center', fontsize=12, fontstyle='italic')

            # Add the title and footer to the entire figure
            fig.text(0.5, 1.028, 'Vagus Hospital', ha='center', fontsize=20, fontweight='bold')
            fig.text(0.5, -0.04, 'Report Analysis by Mediport', ha='center', fontsize=13, fontweight='bold')

            # Draw a border around the entire figure
            border = patches.Rectangle(
                (-0.05, -0.05), 1.1, 1.1,
                transform=fig.transFigure, color='black', linewidth=3, fill=False
            )
            fig.patches.append(border)

            # Adjust layout
            plt.tight_layout()

            # Save the figure to the PDF
            pdf.savefig(fig, bbox_inches='tight', pad_inches=0.5)
            plt.close(fig)

        print(f"Report successfully saved at: {pdf_file_path}")
        return pdf_file_path
    #returns images
    def sumofclaiminitiatedamount(self, df):
        """
        Generates an image report with pivot tables for claim amounts.
        Filters data for years 2022, 2023, and 2024 and provides summaries.
        """
        try:
            # Convert 'Claim Submitted Date' to datetime
            df['Claim Submitted Date'] = pd.to_datetime(df['Claim Submitted Date'], errors='coerce')

            # Extract the year from 'Claim Submitted Date'
            df['Year'] = df['Claim Submitted Date'].dt.year

            # Filter the data for years 2022, 2023, and 2024
            df_filtered = df[df['Year'].isin([2022, 2023, 2024])]

            # Create pivot tables
            pivot_table_filtered = pd.pivot_table(
                df_filtered,
                values='Claim Initaiated Amount(Rs.)',
                index='Case Status',
                columns='Year',
                aggfunc='sum',
                fill_value=0,
                margins=True,
                margins_name='Grand Total'
            )

            pivot_table_all = pd.pivot_table(
                df,
                values='Claim Initaiated Amount(Rs.)',
                index='Case Status',
                aggfunc='sum',
                margins=True,
                margins_name='Total Grand'
            )

            # Create a figure with subplots for both tables
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 14))

            # Hide axes for both tables
            ax1.axis('off')
            ax2.axis('off')

            # Create tables
            table_filtered = ax1.table(
                cellText=pivot_table_filtered.values,
                rowLabels=pivot_table_filtered.index,
                colLabels=pivot_table_filtered.columns,
                loc='center'
            )
            ax1.set_title('Case Status Claim Amt (Filtered: 2022-2024)', fontsize=14, fontweight='bold', pad=20)

            table_all = ax2.table(
                cellText=pivot_table_all.values,
                rowLabels=pivot_table_all.index,
                colLabels=pivot_table_all.columns,
                loc='center'
            )
            ax2.set_title('Case Status Claim Amt (All Data)', fontsize=14, fontweight='bold', pad=20)

            # Adjust table font size and scale
            for table in [table_filtered, table_all]:
                table.auto_set_font_size(False)
                table.set_fontsize(10)
                table.scale(1.3, 1.3)

            # Add descriptive comments
            comment_plot = (
                "The filtered table highlights amounts for the years 2022 to 2024, "
                "while the all-data table provides overall totals."
            )
            fig.text(0.5, 0.55, comment_plot, ha='center', fontsize=12, fontstyle='italic')

            # Add title and footer
            fig.text(0.5, 1.03, 'Vagus Hospital', ha='center', fontsize=20, fontweight='bold')
            fig.text(0.5, 0.01, 'Report Analysis by Mediport', ha='center', fontsize=13, fontweight='bold')

            # Draw a border around the entire figure
            border = patches.Rectangle(
                (-0.05, -0.05), 1.1, 1.1, transform=fig.transFigure,
                color='black', linewidth=3, fill=False
            )
            fig.patches.append(border)

            # Adjust layout and save the figure
            plt.tight_layout()
            reports_folder = os.path.join(os.getcwd(), "Reports")
            os.makedirs(reports_folder, exist_ok=True)

            image_path = os.path.join(reports_folder, "case_status_claim_amt_combined.png")
            plt.savefig(image_path, bbox_inches='tight', pad_inches=0.5)
            print(f'Report saved successfully at: {image_path}')
            return image_path

        except Exception as e:
            print(f"Error in sumofclaiminitiatedamount: {e}")
            return None

    #returns excel
    def Difference_between_claim_initiate_amount_approval_amount(self, df): #generate excel
        # Convert columns to numeric, coercing errors to NaN
        df['Claim Initaiated Amount(Rs.)'] = pd.to_numeric(df['Claim Initaiated Amount(Rs.)'], errors='coerce')
        df['CPD Approved Amount(Rs.)'] = pd.to_numeric(df['CPD Approved Amount(Rs.)'], errors='coerce')

        # Fill NaN values with 0 to avoid issues with subtraction
        df[['Claim Initaiated Amount(Rs.)', 'CPD Approved Amount(Rs.)']] = df[
            ['Claim Initaiated Amount(Rs.)', 'CPD Approved Amount(Rs.)']
        ].fillna(0)

        # Calculate the amount difference
        df['Amount Difference'] = df['Claim Initaiated Amount(Rs.)'] - df['CPD Approved Amount(Rs.)']

        # Create a pivot table
        pivot_table = df.pivot_table(
            index='Case Status',  # Row grouping
            columns='Actual Registration Date',  # Column grouping
            values='Amount Difference',  # Value to aggregate
            aggfunc='sum',  # Aggregation function
            fill_value=0  # Replace missing values with 0
        )

        # Add a new row called 'Total Grand' to calculate the total for each year
        total_amount = pivot_table.sum()
        pivot_table.loc['Total Grand'] = total_amount

        # Ensure the Reports folder exists
        reports_folder = os.path.join(os.getcwd(), "Reports")
        if not os.path.exists(reports_folder):
            os.makedirs(reports_folder)

        # Save the pivot table to an Excel file in the Reports folder
        output_path = os.path.join(reports_folder, 'difference_between_claim_initiated_approved.xlsx')
        pivot_table.to_excel(output_path, sheet_name='Amount Difference')

        print(f"Pivot table saved successfully at: {output_path}")
        return output_path
    #return ExcelFile
    def cases_by_familyid(self,df):   #generate excel
        # Group the data by 'Family Id' and filter where 'Family Id' occurs more than once
        family_counts = df.groupby('Family Id').filter(lambda x: len(x) > 1)

        # Create a pivot table with 'Family Id' as the index
        pivot_table = pd.pivot_table(
            family_counts,
            values=['Case No', 'Claim Initaiated Amount(Rs.)'],
            index='Family Id',
            aggfunc={'Case No': 'count', 'Claim Initaiated Amount(Rs.)': 'sum'},
            fill_value=0
        )

        # Add a 'Grand Total' row
        pivot_table.loc['Grand Total'] = pivot_table.sum()

        # Rename columns for clarity
        pivot_table.columns = ['Count of Cases', 'Total Claim Initiated Amount (Rs.)']

        # Ensure the Reports folder exists
        reports_folder = os.path.join(os.getcwd(), "Reports")
        if not os.path.exists(reports_folder):
            os.makedirs(reports_folder)

        # Save the pivot table to an Excel file in the Reports folder
        output_path = os.path.join(reports_folder, 'case_status_number_and_family_id.xlsx')
        pivot_table.to_excel(output_path, sheet_name='Family Claim Report')

        print(f"Family claim report saved successfully at: {output_path}")
        return output_path

    def combined_report_summary(self,df):
        pdf_files = []
        pdf_files.append(self.report_with_watermark(df,False))
        pdf_files.append(self.save_combined_pivot_tables_as_pdf(df, 'Case Status', 'Gender', 'Case No',False))
        pdf_files.append(self.plot_death_case_distribution(df,False))
        return(self.combine_pdfs(pdf_files))
        # return 'Reports/report_summary.pdf'

    def generate_sample_report(self,df):
        pdf_files=[]
        pdf_files.append(self.report_with_watermark(df))
        pdf_files.append(self.save_combined_pivot_tables_as_pdf(df, 'Case Status', 'Gender', 'Case No'))
        pdf_files.append(self.plot_death_case_distribution(df))
        return(self.combine_pdfs(pdf_files))
# Main function
import os
import zipfile


def main(selected_reports=None, sample=False):
    """
    Main function to handle report generation for both sample and paid reports.
    """
    host = "localhost"
    user = "root"
    password = "1234"
    database = "mediportdb"
    query = "SELECT * FROM casesearch"

    METHOD_MAP = {
        "Cases_Count_by_Status_and_Gender": "count_of_case_status",
        "Cases_Count_by_Age": "count_cases_by_age",
        "Death_Counts_by_Gender": "death_by_gender",
        "Death_Counts_by_Age": "death_by_age",
        "Cases_Count_by_Gender": "count_case_gender",
        "Cases_Count_by_Case_Type": "casecount_by_casetype",
        "Cases_Count_by_Patient_District": "casecount_by_location",
        "Case_Status_Claim_Amount": "casestatus_claim_amount_yearwise",
        "Detailed_Summary_of_Amounts": "sumofclaiminitiatedamount",
        "Combined_Report_Analysis_Summary": "combined_report_summary",
        "Difference_between_claim_initiate_amount_approval_amount":"Difference_between_claim_initiate_amount_approval_amount",
        "cases_by_familyid":"cases_by_familyid",
    }

    connection = DatabaseConnectionSingleton.get_instance(host, user, password, database)

    if not connection:
        print("Failed to connect to the database.")
        return 'Failed to connect to the database!'

    try:
        processor = DataProcessor(connection)
        df = processor.fetch_data(query)
        if df is None:
            print("Failed to fetch data from the database.")
            return 'Failed to fetch data from the database!'

        output_files = []

        # Generate a free sample report
        if sample:
            output_files.append(processor.generate_sample_report(df))
        else:
            # Process selected reports
            for report_name in selected_reports:
                method_name = METHOD_MAP.get(report_name)
                if method_name and hasattr(processor, method_name):
                    method = getattr(processor, method_name)
                    try:
                        output_file = method(df)
                        if output_file:  # Only append if the output_file is not None
                            output_files.append(output_file)
                        else:
                            print(f"Method {method_name} did not return a valid file path.")
                    except Exception as e:
                        print(f"An error occurred while executing {method_name}: {e}")
                else:
                    print(f"Method {method_name} not found in DataProcessor.")

            # Combine PDFs if applicable
            pdf_files = [file for file in output_files if file.endswith('.pdf')]
            if pdf_files:
                combined_pdf_path = processor.combine_pdfs(pdf_files)
                if combined_pdf_path:
                    print(f"Combined PDF saved at {combined_pdf_path}")

                    # Remove individual PDFs
                    for pdf in pdf_files:
                        if pdf != combined_pdf_path:  # Skip the combined PDF
                            try:
                                os.remove(pdf)
                                print(f"{pdf} is deleted successfully")
                            except Exception as e:
                                print(f"Error deleting {pdf}: {e}")

                    # Update output_files to only include the combined PDF and non-PDF files
                    output_files = [file for file in output_files if not file.endswith('.pdf')]
                    output_files.append(combined_pdf_path)
            else:
                print("No valid PDFs to combine.")

        # Create a zip file containing all output files
        zip_file_path = "Reports/Combined_Files.zip"
        with zipfile.ZipFile(zip_file_path, 'w') as zipf:
            for file in output_files:
                if os.path.exists(file):
                    zipf.write(file, os.path.basename(file))

        print(f"All files have been zipped into {zip_file_path}")
        return 'Reports generated successfully!'

    except Exception as e:
        print(f"An error occurred: {e}")
        return 'An error occurred while generating reports!'

    finally:
        DatabaseConnectionSingleton.close_instance()


# Run the main function
if __name__ == "__main__":
    main()
