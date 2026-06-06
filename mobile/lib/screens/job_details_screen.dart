import 'package:flutter/material.dart';

/// Placeholder for job details screen.
class JobDetailsScreen extends StatelessWidget {
  static const routeName = '/job-details';
  final String jobId;
  final String jobTitle;
  const JobDetailsScreen({
    super.key,
    this.jobId = '',
    this.jobTitle = '',
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(jobTitle.isEmpty ? 'Job Details' : jobTitle)),
      body: Center(child: Text('Job Details for $jobId (placeholder)')),
    );
  }
}
