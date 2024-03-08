import sys
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QTableWidget,
                             QTableWidgetItem, QLineEdit, QHBoxLayout, QTextEdit, QGridLayout, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

class Costs:
    def __init__(self, gap_cost, matrix):
        self.matrix = matrix
        self.gap_cost = gap_cost
        self.base_to_index = {'A': 0, 'C': 1, 'G': 2, 'T': 3}
        self.history = [] # Initialize a history stack

class SequenceAlignmentApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sequence Alignment Visualization")
        self.setGeometry(100, 100, 1000, 600)  # Adjusted window size

        # Main widget and layout
        self.centralWidget = QWidget(self)
        self.setCentralWidget(self.centralWidget)
        self.gridLayout = QGridLayout()
        self.centralWidget.setLayout(self.gridLayout)

        # UI components
        self.setupUI()

        # Automatically set default input values for testing
        self.seq1Input.setText("TCCAGAGA")
        self.seq2Input.setText("TCGAT")
        self.gapCostInput.setText("-5")
        self.subMatrixInput.setPlainText("10 2 5 2; 2 10 2 5; 5 2 10 2; 2 5 2 10")

    def setupUI(self):
        # Input layout
        self.inputLayout = QVBoxLayout()
        self.matrixInputLayout = QVBoxLayout()

        # Sequence input fields
        self.seq1Input = QLineEdit(self)
        self.seq2Input = QLineEdit(self)
        self.gapCostInput = QLineEdit(self)
        self.subMatrixInput = QTextEdit(self)
        self.subMatrixInput.setPlaceholderText("10 2 5 2; 2 10 2 5; 5 2 10 2; 2 5 2 10")

        # Finish button, if a user does not want to see all the steps, they should be able to just click this and finish the alignment
        self.finishButton = QPushButton("Finish All Score Steps", self)
        self.finishButton.clicked.connect(self.finishAlignment)
        self.finishButton.setEnabled(False)  # Disabled until "Start" is pressed
        self.matrixInputLayout.addWidget(self.finishButton)

        # Step back button
        self.goBackButton = QPushButton("Go Back", self)
        self.goBackButton.clicked.connect(self.goBackStep)
        self.goBackButton.setEnabled(True)  # Initially disabled
        self.matrixInputLayout.addWidget(self.goBackButton)

        # Start button
        self.startButton = QPushButton("Start", self)
        self.startButton.clicked.connect(self.startAlignment)

        # Next Step button
        self.nextStepButton = QPushButton("Next Step", self)
        self.nextStepButton.clicked.connect(self.nextAlignmentStep)
        self.nextStepButton.setEnabled(False)  # Disabled until "Start" is pressed

        # Explanation display
        self.explanationDisplay = QLabel("Explanation will be shown here.", self)
        self.explanationDisplay.setWordWrap(True)  # Enable word-wrap for longer explanations
        self.gridLayout.addWidget(self.explanationDisplay, 4, 0, 1, 3)

        # Adding widgets to layouts
        self.inputLayout.addWidget(QLabel("Sequence 1:"))
        self.inputLayout.addWidget(self.seq1Input)
        self.inputLayout.addWidget(QLabel("Sequence 2:"))
        self.inputLayout.addWidget(self.seq2Input)
        self.inputLayout.addWidget(QLabel("Gap Cost:"))
        self.inputLayout.addWidget(self.gapCostInput)
        self.matrixInputLayout.addWidget(QLabel("Substitution Matrix:"))
        self.matrixInputLayout.addWidget(self.subMatrixInput)
        self.matrixInputLayout.addWidget(self.startButton)
        self.matrixInputLayout.addWidget(self.nextStepButton)

        # Combine input layouts into the grid
        self.gridLayout.addLayout(self.inputLayout, 0, 0, 1, 1)
        self.gridLayout.addLayout(self.matrixInputLayout, 0, 1, 1, 2)

        # Placeholder for displaying the inputs and a separator
        self.inputsDisplay = QLabel("", self)
        self.gridLayout.addWidget(self.inputsDisplay, 1, 0, 1, 3)

        # Visual separator
        self.separator = QFrame(self)
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setFrameShadow(QFrame.Sunken)
        self.gridLayout.addWidget(self.separator, 2, 0, 1, 3)

        # Placeholder for DP table setup
        self.dpTable = None

    def goBackStep(self):
        if self.history:
            # Remove the last entry from the history to get the indices and value before the last change
            i, j, prev_value = self.history.pop()

            # Restore the previous value of the cell
            self.dpTableResults[i, j] = prev_value
            self.dpTable.setItem(i, j, QTableWidgetItem(str(prev_value)))

            # Enable the "Next Step" button again if it was disabled
            self.nextStepButton.setEnabled(True)

            # If the history is now empty, disable the "Go Back" button
            if not self.history:
                self.goBackButton.setEnabled(False)

            # Adjust currentStepI and currentStepJ to point to the previous step
            if self.currentStepJ == 0:
                self.currentStepI -= 1
                self.currentStepJ = len(self.seq2)  # Assuming seq2 is the horizontal sequence
            else:
                self.currentStepJ -= 1

            # Highlight the cell that is now the current step
            self.highlightCell(self.currentStepI, self.currentStepJ)

            # Update the explanation to reflect the step we've gone back to
            if self.currentStepI == 0 or self.currentStepJ == 0:
                self.explanationDisplay.setText("This is the start of a row or column, initialized with gap costs.")
            else:
                self.explanationDisplay.setText("Ready to calculate this cell.")

            # Since we have moved back a step, we need to re-enable the "Go Back" button if there are more steps to undo
            if self.history:
                self.goBackButton.setEnabled(True)
            else:
                self.goBackButton.setEnabled(False)
    def highlightCell(self, i, j):
        # Reset all cell backgrounds to default
        for row in range(self.dpTable.rowCount()):
            for col in range(self.dpTable.columnCount()):
                self.dpTable.item(row, col).setBackground(QColor(255, 255, 255))
        # Highlight the current cell
        if i < self.dpTable.rowCount() and j < self.dpTable.columnCount():
            self.dpTable.item(i, j).setBackground(QColor(255, 255, 0))  # Yellow

    def finishAlignment(self):
        try:
            for i in range(1, len(self.seq1) + 1):
                for j in range(1, len(self.seq2) + 1):
                    match_mismatch_cost = self.calculateStepCost(self.seq1[i - 1], self.seq2[j - 1])
                    match_mismatch = self.dpTableResults[i - 1, j - 1] + match_mismatch_cost
                    delete = self.dpTableResults[i - 1, j] + self.costs.gap_cost
                    insert = self.dpTableResults[i, j - 1] + self.costs.gap_cost

                    # Choose the best cost and update the DP table
                    self.dpTableResults[i, j] = max(match_mismatch, delete, insert)

                    # Update the table widget item directly without intermediate steps
                    self.dpTable.setItem(i, j, QTableWidgetItem(str(self.dpTableResults[i, j])))

            # Highlight the final score cell in the bottom-right corner
            self.highlightCell(len(self.seq1), len(self.seq2))

            # Update explanation for the completion
            self.explanationDisplay.setText(
                "Alignment completed. Final score is shown in the bottom-right corner of the table.")

            # Disable the Next Step and Finish buttons as the calculation is complete
            self.nextStepButton.setEnabled(False)
            self.finishButton.setEnabled(False)
        except Exception as e:
            print(f"Error in finishAlignment: {e}")

    def startAlignment(self):
        try:
            self.seq1 = self.seq1Input.text()
            self.seq2 = self.seq2Input.text()
            gapCost = float(self.gapCostInput.text())

            # Parsing the substitution matrix from the text input
            matrixStr = self.subMatrixInput.toPlainText()
            matrixRows = matrixStr.split(';')
            matrix = np.array([row.split() for row in matrixRows], dtype=float)
            self.costs = Costs(gap_cost=gapCost, matrix=matrix)

            inputsSummary = f"Sequence 1: {self.seq1}\nSequence 2: {self.seq2}\nGap Cost: {gapCost}\nSubstitution Matrix:\n{matrixStr}"
            self.inputsDisplay.setText(inputsSummary)

            self.createOrUpdateDPTable(self.seq1, self.seq2)
            self.nextStepButton.setEnabled(True)  # Enable the "Next Step" button after starting

            self.currentStepI = 0
            self.currentStepJ = 0

            self.dpTableResults = np.full((len(self.seq1) + 1, len(self.seq2) + 1), np.NaN)
            self.dpTableResults[0, :] = np.arange(len(self.seq2) + 1) * self.costs.gap_cost
            self.dpTableResults[:, 0] = np.arange(len(self.seq1) + 1) * self.costs.gap_cost
            for i in range(len(self.seq1) + 1):
                for j in range(len(self.seq2) + 1):
                    self.dpTable.setItem(i, j, QTableWidgetItem(str(self.dpTableResults[i, j])))
            self.currentStepI, self.currentStepJ = 1, 0  # Start from the first cell after initialized edges
            self.history = []  # Reset the history stack when starting a new alignment
            self.finishButton.setEnabled(True)
        except Exception as e:
            print(f"Error in startAlignment: {e}")

    def nextAlignmentStep(self):
        try:
            if self.currentStepI < len(self.seq1) + 1 and self.currentStepJ < len(self.seq2) + 1:
                explanation = ""
                if self.currentStepI > 0 and self.currentStepJ > 0:
                    # Calculate costs for match/mismatch, insertion, and deletion
                    match_mismatch_cost = self.calculateStepCost(self.seq1[self.currentStepI - 1],
                                                                 self.seq2[self.currentStepJ - 1])
                    match_mismatch = self.dpTableResults[self.currentStepI - 1, self.currentStepJ - 1] + match_mismatch_cost
                    delete = self.dpTableResults[self.currentStepI - 1, self.currentStepJ] + self.costs.gap_cost
                    insert = self.dpTableResults[self.currentStepI, self.currentStepJ - 1] + self.costs.gap_cost
                    max_cost = max(match_mismatch, delete, insert)

                    # Before we update the table, we need to store the current state in the history stack
                    prev_value = self.dpTableResults[self.currentStepI, self.currentStepJ]
                    self.history.append((self.currentStepI, self.currentStepJ, prev_value))

                    self.dpTableResults[self.currentStepI, self.currentStepJ] = max_cost

                    # Construct the explanation based on which option was chosen
                    if max_cost == match_mismatch:
                        explanation = f"Match/mismatch between {self.seq1[self.currentStepI - 1]} and {self.seq2[self.currentStepJ - 1]}. Cost: {match_mismatch_cost}."
                    elif max_cost == delete:
                        explanation = "Deletion. Using gap cost."
                    elif max_cost == insert:
                        explanation = "Insertion. Using gap cost."

                    self.dpTable.setItem(self.currentStepI, self.currentStepJ, QTableWidgetItem(str(max_cost)))
                    self.highlightCell(self.currentStepI, self.currentStepJ)

                else:
                    # Handling the initial row and column where only gaps can occur
                    if self.currentStepI == 0 or self.currentStepJ == 0:
                        explanation = "Starting row/column, using gap costs."

                self.explanationDisplay.setText(explanation)  # Update the explanation display
                self.currentStepJ += 1

                if self.currentStepJ == len(self.seq2) + 1:
                    self.currentStepJ = 0
                    self.currentStepI += 1
                if self.currentStepI == len(self.seq1) + 1:
                    self.nextStepButton.setEnabled(False)  # Disable the button if finished
            else:
                self.nextStepButton.setEnabled(False)  # Disable the button if finished
        except Exception as e:
            print(f"Error in nextAlignmentStep: {e}")

    def calculateStepCost(self, base_1, base_2):
        try:
            index_2 = self.costs.base_to_index[base_2]
            index_1 = self.costs.base_to_index[base_1]
            cost = self.costs.matrix[index_1, index_2]
            return cost
        except Exception as e:
            print(f"Error in calculateStepCost: {e}")
            return 0.0  # Return a default value to avoid NoneType issues

    def updateExplanation(self, i, j):
        # Update the UI with an explanation of how the current cell's value was calculated
        explanation = f"Calculating cell [{i + 1}, {j + 1}]: ..."
        # TODO - Display this explanation somewhere in the UI that makes sense...

    def createOrUpdateDPTable(self, seq1, seq2):
        rows, cols = len(seq1) + 1, len(seq2) + 1
        if self.dpTable:
            self.gridLayout.removeWidget(self.dpTable)
            self.dpTable.deleteLater()

        self.dpTable = QTableWidget(rows, cols, self)
        self.dpTable.setHorizontalHeaderLabels([' '] + list(seq2))
        self.dpTable.setVerticalHeaderLabels([' '] + list(seq1))
        for i in range(rows):
            for j in range(cols):
                item = QTableWidgetItem("")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.dpTable.setItem(i, j, item)

        self.gridLayout.addWidget(self.dpTable, 3, 0, 1, 3)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = SequenceAlignmentApp()
    mainWindow.show()
    sys.exit(app.exec_())
