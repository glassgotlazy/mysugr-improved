import 'dart:io';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:csv/csv.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:google_fonts/google_fonts.dart';

void main() {
  runApp(const MySugrApp());
}

class MySugrApp extends StatelessWidget {
  const MySugrApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: "MySugr AI Coach",
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        textTheme: GoogleFonts.poppinsTextTheme(),
        primarySwatch: Colors.teal,
      ),
      home: const HomeScreen(),
    );
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  List<List<dynamic>> _csvData = [];
  List<double> glucoseValues = [];

  Future<void> _pickCSV() async {
    FilePickerResult? result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['csv'],
    );

    if (result != null) {
      final file = File(result.files.single.path!);
      final content = await file.readAsString();
      List<List<dynamic>> rows = const CsvToListConverter().convert(content);

      setState(() {
        _csvData = rows;
        glucoseValues = rows.skip(1).map((r) => (r[3] as num).toDouble()).toList();
      });
    }
  }

  double insulinNeeded(double currentGlucose, {double targetGlucose = 150, double isf = 14.13}) {
    if (currentGlucose <= targetGlucose) return 0.0;
    return (currentGlucose - targetGlucose) / isf;
  }

  String dietSuggestion(double glucose) {
    if (glucose > 250) {
      return "❌ High glucose!\nAvoid sweets, white rice, bread.\nEat leafy vegetables, salads, and light proteins.";
    } else if (glucose < 80) {
      return "⚠️ Low glucose!\nEat 15g fast carbs (banana, glucose tablet, juice). Recheck after 15 mins.";
    } else {
      return "✅ Normal glucose!\nBalanced diet: whole grains, lean proteins, veggies, nuts.";
    }
  }

  @override
  Widget build(BuildContext context) {
    double latestGlucose = glucoseValues.isNotEmpty ? glucoseValues.last : 0.0;

    return Scaffold(
      appBar: AppBar(
        title: const Text("MySugr AI Coach"),
        centerTitle: true,
        elevation: 4,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            ElevatedButton.icon(
              icon: const Icon(Icons.upload_file),
              label: const Text("Upload MySugr CSV"),
              onPressed: _pickCSV,
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 20),
                textStyle: const TextStyle(fontSize: 16),
              ),
            ),
            const SizedBox(height: 20),

            if (glucoseValues.isNotEmpty) ...[
              Text(
                "Latest Glucose: ${latestGlucose.toStringAsFixed(1)} mg/dL",
                style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 10),

              SizedBox(
                height: 200,
                child: LineChart(
                  LineChartData(
                    borderData: FlBorderData(show: false),
                    gridData: FlGridData(show: true),
                    titlesData: FlTitlesData(show: false),
                    lineBarsData: [
                      LineChartBarData(
                        spots: glucoseValues.asMap().entries.map((e) => FlSpot(e.key.toDouble(), e.value)).toList(),
                        isCurved: true,
                        color: Colors.teal,
                        dotData: FlDotData(show: false),
                        belowBarData: BarAreaData(show: true, color: Colors.teal.withOpacity(0.3)),
                      )
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 20),

              Card(
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                elevation: 5,
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    children: [
                      const Text("💉 Insulin Correction Suggestion",
                          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 10),
                      Text(
                        "${insulinNeeded(latestGlucose).toStringAsFixed(1)} units suggested",
                        style: const TextStyle(fontSize: 16),
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 20),

              Card(
                color: Colors.teal.shade50,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                elevation: 3,
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Text(
                    dietSuggestion(latestGlucose),
                    style: const TextStyle(fontSize: 16),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
