import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:provider/provider.dart';

import '../api/client.dart';
import '../widgets/score_card.dart';

/// Resume upload + ATS score screen.
///
/// Flow:
/// 1. User taps "Upload Resume" → file picker (PDF/DOCX)
/// 2. Client uploads to /resumes endpoint
/// 3. User pastes/types a job description
/// 4. Tap "Score Match" → POST /resumes/{id}/score
/// 5. Display: score, grade, matched/missing skills, suggestions
class ResumeScoreScreen extends StatefulWidget {
  static const routeName = '/resume-score';
  const ResumeScoreScreen({super.key});

  @override
  State<ResumeScoreScreen> createState() => _ResumeScoreScreenState();
}

class _ResumeScoreScreenState extends State<ResumeScoreScreen> {
  PlatformFile? _pickedFile;
  Resume? _uploadedResume;
  final _jobDescriptionController = TextEditingController();
  AtsScore? _score;
  bool _uploading = false;
  bool _scoring = false;
  String? _error;

  @override
  void dispose() {
    _jobDescriptionController.dispose();
    super.dispose();
  }

  Future<void> _pickFile() async {
    setState(() => _error = null);
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf', 'docx', 'doc', 'txt'],
        withData: true,
      );
      if (result == null || result.files.isEmpty) return;
      setState(() {
        _pickedFile = result.files.first;
        _uploadedResume = null;
        _score = null;
      });
    } catch (e) {
      setState(() => _error = 'File pick failed: $e');
    }
  }

  Future<void> _uploadAndScore() async {
    if (_pickedFile == null) {
      setState(() => _error = 'Pick a resume file first');
      return;
    }
    if (_jobDescriptionController.text.trim().length < 30) {
      setState(() => _error = 'Paste a job description (≥30 chars)');
      return;
    }

    setState(() {
      _uploading = true;
      _error = null;
    });
    final api = context.read<ApiClient>();
    try {
      final resume = await api.uploadResume(_pickedFile!);
      setState(() {
        _uploadedResume = resume;
        _uploading = false;
        _scoring = true;
      });

      final score = await api.scoreResume(
        resume.id,
        _jobDescriptionController.text,
      );
      setState(() {
        _score = score;
        _scoring = false;
      });
    } catch (e) {
      setState(() {
        _uploading = false;
        _scoring = false;
        _error = 'Failed: $e';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Resume ATS Score')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Step 1: Upload Resume',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
            ),
            const SizedBox(height: 8),
            OutlinedButton.icon(
              onPressed: _uploading ? null : _pickFile,
              icon: const Icon(Icons.upload_file),
              label: Text(_pickedFile?.name ?? 'Choose PDF / DOCX / TXT'),
            ),
            if (_uploadedResume != null) ...[
              const SizedBox(height: 8),
              Row(
                children: [
                  const Icon(Icons.check_circle,
                      color: Colors.green, size: 18),
                  const SizedBox(width: 4),
                  Expanded(
                    child: Text(
                      'Uploaded: ${_uploadedResume!.fileName}',
                      style: const TextStyle(fontSize: 13),
                    ),
                  ),
                ],
              ),
            ],
            const SizedBox(height: 24),

            Text(
              'Step 2: Paste Job Description',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _jobDescriptionController,
              maxLines: 8,
              decoration: const InputDecoration(
                hintText:
                    'Paste the full job description here...\n\n(e.g. "Senior Backend Engineer with 5+ years of Python...")',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),

            if (_error != null)
              Card(
                color: Colors.red.shade50,
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Row(
                    children: [
                      const Icon(Icons.error, color: Colors.red),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          _error!,
                          style: const TextStyle(color: Colors.red),
                        ),
                      ),
                    ],
                  ),
                ),
              ),

            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: (_uploading || _scoring) ? null : _uploadAndScore,
                icon: _uploading || _scoring
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : const Icon(Icons.analytics),
                label: Text(_uploading
                    ? 'Uploading…'
                    : _scoring
                        ? 'Scoring…'
                        : 'Score Match'),
              ),
            ),
            const SizedBox(height: 24),

            if (_score != null) _buildScoreSection(),
          ],
        ),
      ),
    );
  }

  Widget _buildScoreSection() {
    final s = _score!;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Result',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
        ),
        const SizedBox(height: 8),
        ScoreCard(
          score: s.overall,
          grade: s.grade,
          label: 'Match score',
          matchedCount: s.matchedSkills.length,
          missingCount: s.missingSkills.length,
        ),
        const SizedBox(height: 16),

        if (s.matchedSkills.isNotEmpty) ...[
          Text(
            'Matched Skills (${s.matchedSkills.length})',
            style: const TextStyle(fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 4),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: s.matchedSkills
                .map((s) => Chip(
                      label: Text(s),
                      backgroundColor: Colors.green.shade50,
                      side: BorderSide(color: Colors.green.shade300),
                    ))
                .toList(),
          ),
          const SizedBox(height: 12),
        ],

        if (s.missingSkills.isNotEmpty) ...[
          Text(
            'Missing Skills (${s.missingSkills.length})',
            style: const TextStyle(fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 4),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: s.missingSkills
                .map((s) => Chip(
                      label: Text(s),
                      backgroundColor: Colors.red.shade50,
                      side: BorderSide(color: Colors.red.shade300),
                    ))
                .toList(),
          ),
          const SizedBox(height: 12),
        ],

        if (s.suggestions.isNotEmpty) ...[
          Text(
            'Suggestions',
            style: const TextStyle(fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 4),
          ...s.suggestions.map((s) => Card(
                margin: const EdgeInsets.only(bottom: 8),
                child: ListTile(
                  leading: Icon(
                    s.severity == 'critical' || s.severity == 'high'
                        ? Icons.priority_high
                        : Icons.info_outline,
                    color: s.severity == 'critical' || s.severity == 'high'
                        ? Colors.red
                        : Colors.amber,
                  ),
                  title: Text(s.title),
                  subtitle: Text(s.message),
                  isThreeLine: s.message.length > 50,
                ),
              )),
        ],
      ],
    );
  }
}
