import 'package:flutter/material.dart';

/// QR scanner placeholder — real implementation would use mobile_scanner.
class QrScannerScreen extends StatelessWidget {
  static const routeName = '/qr-scan';
  const QrScannerScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Scan Job QR')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.qr_code_scanner, size: 80, color: Colors.grey.shade400),
            const SizedBox(height: 16),
            const Text('QR scanner placeholder'),
            const SizedBox(height: 8),
            Text('Real impl would use mobile_scanner',
                style: TextStyle(color: Colors.grey.shade600, fontSize: 12)),
          ],
        ),
      ),
    );
  }
}
