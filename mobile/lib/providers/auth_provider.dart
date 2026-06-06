import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../api/client.dart';

/// Authentication state holder.
class AuthProvider extends ChangeNotifier {
  final ApiClient api;
  final SharedPreferences prefs;
  bool _isAuthenticated = false;
  String? _token;
  String? _userId;

  AuthProvider(this.api, this.prefs) {
    _token = prefs.getString('auth_token');
    _isAuthenticated = _token != null;
  }

  bool get isAuthenticated => _isAuthenticated;
  String? get token => _token;
  String? get userId => _userId;

  Future<bool> login(String email, String password) async {
    final result = await api.login(email, password);
    if (result.isSuccess && result.data != null) {
      _token = result.data!;
      _isAuthenticated = true;
      await prefs.setString('auth_token', _token!);
      notifyListeners();
      return true;
    }
    return false;
  }

  Future<void> logout() async {
    _token = null;
    _userId = null;
    _isAuthenticated = false;
    await prefs.remove('auth_token');
    notifyListeners();
  }
}
