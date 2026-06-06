import 'package:flutter/foundation.dart';

import '../api/client.dart';

/// Cached list of jobs.
class JobProvider extends ChangeNotifier {
  final List<Job> _jobs = [];
  List<Job> get jobs => List.unmodifiable(_jobs);

  bool _loading = false;
  bool get loading => _loading;

  void setLoading(bool v) {
    _loading = v;
    notifyListeners();
  }

  void setJobs(List<Job> jobs) {
    _jobs.clear();
    _jobs.addAll(jobs);
    notifyListeners();
  }
}
