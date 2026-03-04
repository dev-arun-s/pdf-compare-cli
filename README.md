# pdf-compare-cli
✅ How To Build
cd pdf-compare-cli
mvn clean package

This produces:
target/pdf-compare-cli-1.0.0.jar

✅ How To Run
java -jar target/pdf-compare-cli-1.0.0.jar \
  --file1 old.pdf \
  --file2 new.pdf \
  --diff-output diff.pdf \
  --report report.json

