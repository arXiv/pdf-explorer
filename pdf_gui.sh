source /home/markn/Documents/arxiv/arxiv/bin/activate
python /home/markn/Documents/arxiv/pdf_gui.py $1
a=$1
firefox "${a%.pdf}.html"