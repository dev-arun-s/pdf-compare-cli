package com.example.pdfcompare;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.rendering.PDFRenderer;

import java.awt.image.BufferedImage;
import java.io.File;
import java.util.HashMap;
import java.util.Map;

public class PdfCompareCli {

    public static void main(String[] args) throws Exception {

        if (args.length < 8) {
            System.out.println("Usage:");
            System.out.println("java -jar pdf-compare-cli.jar --file1 old.pdf --file2 new.pdf "
                    + "--diff-output diff.pdf --report report.json");
            System.exit(2);
        }

        Map<String, String> params = parseArgs(args);

        File file1 = new File(params.get("--file1"));
        File file2 = new File(params.get("--file2"));
        File diffFile = new File(params.get("--diff-output"));
        File reportFile = new File(params.get("--report"));

        ComparisonResult result = compare(file1, file2, diffFile);

        ObjectMapper mapper = new ObjectMapper();
        mapper.writerWithDefaultPrettyPrinter().writeValue(reportFile, result);

        if (result.identical) {
            System.out.println("PDFs are identical.");
            System.exit(0);
        } else {
            System.out.println("Differences detected.");
            System.exit(1);
        }
    }

    private static ComparisonResult compare(File f1, File f2, File diffOut) throws Exception {

        try (PDDocument doc1 = PDDocument.load(f1);
             PDDocument doc2 = PDDocument.load(f2);
             PDDocument diffDoc = new PDDocument()) {

            PDFRenderer r1 = new PDFRenderer(doc1);
            PDFRenderer r2 = new PDFRenderer(doc2);

            int pages = Math.min(doc1.getNumberOfPages(), doc2.getNumberOfPages());
            int diffPages = 0;
            double totalDiffPercent = 0;

            for (int i = 0; i < pages; i++) {

                BufferedImage img1 = r1.renderImageWithDPI(i, 150);
                BufferedImage img2 = r2.renderImageWithDPI(i, 150);

                double diffPercent = compareImages(img1, img2);

                totalDiffPercent += diffPercent;

                if (diffPercent > 0) diffPages++;

                diffDoc.addPage(doc1.getPage(i));
            }

            diffDoc.save(diffOut);

            ComparisonResult result = new ComparisonResult();
            result.identical = diffPages == 0;
            result.pagesCompared = pages;
            result.pagesWithDifferences = diffPages;
            result.overallDifferencePercent = totalDiffPercent / pages;

            return result;
        }
    }

    private static double compareImages(BufferedImage img1, BufferedImage img2) {

        int width = Math.min(img1.getWidth(), img2.getWidth());
        int height = Math.min(img1.getHeight(), img2.getHeight());

        long diffPixels = 0;

        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                if (img1.getRGB(x, y) != img2.getRGB(x, y)) {
                    diffPixels++;
                }
            }
        }

        return (double) diffPixels / (width * height) * 100;
    }

    private static Map<String, String> parseArgs(String[] args) {
        Map<String, String> map = new HashMap<>();
        for (int i = 0; i < args.length - 1; i += 2) {
            map.put(args[i], args[i + 1]);
        }
        return map;
    }

    public static class ComparisonResult {
        public boolean identical;
        public int pagesCompared;
        public int pagesWithDifferences;
        public double overallDifferencePercent;
    }
}
