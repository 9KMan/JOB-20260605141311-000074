import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

/// API Response wrapper for type-safe handling
class ApiResponse<T> {
  final T? data;
  final String? error;
  final int statusCode;
  
  ApiResponse.success(this.data, this.statusCode);
  ApiResponse.failure(this.error, this.statusCode);
  
  bool get isSuccess => statusCode >= 200 && statusCode < 300;
}

/// Resume data model
class Resume {
  final String id;
  final String fileName;
  final String fileUrl;
  final DateTime uploadedAt;
  final AtsScore? score;
  
  Resume({
    required this.id,
    required this.fileName,
    required this.fileUrl,
    required this.uploadedAt,
    this.score,
  });
  
  factory Resume.fromJson(Map<String, dynamic> json) {
    return Resume(
      id: json['id'] ?? '',
      fileName: json['file_name'] ?? 'resume.pdf',
      fileUrl: json['file_url'] ?? '',
      uploadedAt: json['uploaded_at'] != null 
          ? DateTime.parse(json['uploaded_at']) 
          : DateTime.now(),
      score: json['score'] != null ? AtsScore.fromJson(json['score']) : null,
    );
  }
  
  Map<String, dynamic> toJson() => {
    'id': id,
    'file_name': fileName,
    'file_url': fileUrl,
    'uploaded_at': uploadedAt.toIso8601String(),
    'score': score?.toJson(),
  };
}

/// ATS Score data model
class AtsScore {
  final int overallScore;
  final int? keywordsScore;
  final int? formatScore;
  final int? experienceScore;
  final int? educationScore;
  final List<String> matchedKeywords;
  final List<String> missingKeywords;
  final List<String> suggestions;
  
  AtsScore({
    required this.overallScore,
    this.keywordsScore,
    this.formatScore,
    this.experienceScore,
    this.educationScore,
    this.matchedKeywords = const [],
    this.missingKeywords = const [],
    this.suggestions = const [],
  });
  
  factory AtsScore.fromJson(Map<String, dynamic> json) {
    return AtsScore(
      overallScore: json['overall_score'] ?? 0,
      keywordsScore: json['keywords_score'],
      formatScore: json['format_score'],
      experienceScore: json['experience_score'],
      educationScore: json['education_score'],
      matchedKeywords: List<String>.from(json['matched_keywords'] ?? []),
      missingKeywords: List<String>.from(json['missing_keywords'] ?? []),
      suggestions: List<String>.from(json['suggestions'] ?? []),
    );
  }
  
  Map<String, dynamic> toJson() => {
    'overall_score': overallScore,
    'keywords_score': keywordsScore,
    'format_score': formatScore,
    'experience_score': experienceScore,
    'education_score': educationScore,
    'matched_keywords': matchedKeywords,
    'missing_keywords': missingKeywords,
    'suggestions': suggestions,
  };
  
  String get letterGrade {
    if (overallScore >= 90) return 'A';
    if (overallScore >= 80) return 'B';
    if (overallScore >= 70) return 'C';
    if (overallScore >= 60) return 'D';
    return 'F';
  }
}

/// Job listing data model
class Job {
  final String id;
  final String title;
  final String company;
  final String location;
  final String? description;
  final String? salary;
  final String? jobType;
  final DateTime postedAt;
  final AtsScore? matchScore;
  final bool isSaved;
  
  Job({
    required this.id,
    required this.title,
    required this.company,
    required this.location,
    this.description,
    this.salary,
    this.jobType,
    required this.postedAt,
    this.matchScore,
    this.isSaved = false,
  });
  
  factory Job.fromJson(Map<String, dynamic> json) {
    return Job(
      id: json['id'] ?? '',
      title: json['title'] ?? '',
      company: json['company'] ?? '',
      location: json['location'] ?? '',
      description: json['description'],
      salary: json['salary'],
      jobType: json['job_type'],
      postedAt: json['posted_at'] != null 
          ? DateTime.parse(json['posted_at']) 
          : DateTime.now(),
      matchScore: json['match_score'] != null 
          ? AtsScore.fromJson(json['match_score']) 
          : null,
      isSaved: json['is_saved'] ?? false,
    );
  }
  
  Map<String, dynamic> toJson() => {
    'id': id,
    'title': title,
    'company': company,
    'location': location,
    'description': description,
    'salary': salary,
    'job_type': jobType,
    'posted_at': postedAt.toIso8601String(),
    'match_score': matchScore?.toJson(),
    'is_saved': isSaved,
  };
}

/// API Client for communicating with the backend
class ApiClient {
  final String baseUrl;
  final bool useMockData;
  String? _authToken;
  final http.Client _httpClient;
  
  ApiClient({
    required this.baseUrl,
    required this.useMockData,
    http.Client? client,
  }) : _httpClient = client ?? http.Client();
  
  void setAuthToken(String? token) {
    _authToken = token;
  }
  
  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    if (_authToken != null) 'Authorization': 'Bearer $_authToken',
  };
  
  // ============ AUTH ENDPOINTS ============
  
  Future<ApiResponse<Map<String, dynamic>>> login({
    required String email,
    required String password,
  }) async {
    if (useMockData) {
      await Future.delayed(const Duration(milliseconds: 800));
      if (email.isNotEmpty && password.length >= 6) {
        return ApiResponse.success({
          'token': 'mock_jwt_token_${DateTime.now().millisecondsSinceEpoch}',
          'user': {
            'id': 'user_123',
            'email': email,
            'name': 'Demo User',
          },
        }, 200);
      }
      return ApiResponse.failure('Invalid credentials', 401);
    }
    
    try {
      final response = await _httpClient.post(
        Uri.parse('$baseUrl/auth/login'),
        headers: _headers,
        body: jsonEncode({'email': email, 'password': password}),
      );
      
      if (response.statusCode == 200) {
        return ApiResponse.success(
          jsonDecode(response.body),
          response.statusCode,
        );
      }
      return ApiResponse.failure(
        jsonDecode(response.body)['detail'] ?? 'Login failed',
        response.statusCode,
      );
    } on SocketException {
      return ApiResponse.failure('No internet connection', 0);
    } catch (e) {
      return ApiResponse.failure('An error occurred: $e', 0);
    }
  }
  
  Future<ApiResponse<Map<String, dynamic>>> register({
    required String email,
    required String password,
    required String name,
  }) async {
    if (useMockData) {
      await Future.delayed(const Duration(milliseconds: 800));
      return ApiResponse.success({
        'token': 'mock_jwt_token_${DateTime.now().millisecondsSinceEpoch}',
        'user': {
          'id': 'user_${DateTime.now().millisecondsSinceEpoch}',
          'email': email,
          'name': name,
        },
      }, 201);
    }
    
    try {
      final response = await _httpClient.post(
        Uri.parse('$baseUrl/auth/register'),
        headers: _headers,
        body: jsonEncode({
          'email': email,
          'password': password,
          'name': name,
        }),
      );
      
      if (response.statusCode == 201) {
        return ApiResponse.success(
          jsonDecode(response.body),
          response.statusCode,
        );
      }
      return ApiResponse.failure(
        jsonDecode(response.body)['detail'] ?? 'Registration failed',
        response.statusCode,
      );
    } on SocketException {
      return ApiResponse.failure('No internet connection', 0);
    } catch (e) {
      return ApiResponse.failure('An error occurred: $e', 0);
    }
  }
  
  // ============ RESUME ENDPOINTS ============
  
  Future<ApiResponse<List<Resume>>> getResumes() async {
    if (useMockData) {
      await Future.delayed(const Duration(milliseconds: 600));
      return ApiResponse.success(_mockResumes, 200);
    }
    
    try {
      final response = await _httpClient.get(
        Uri.parse('$baseUrl/resumes'),
        headers: _headers,
      );
      
      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return ApiResponse.success(
          data.map((json) => Resume.fromJson(json)).toList(),
          response.statusCode,
        );
      }
      return ApiResponse.failure('Failed to fetch resumes', response.statusCode);
    } on SocketException {
      return ApiResponse.failure('No internet connection', 0);
    } catch (e) {
      return ApiResponse.failure('An error occurred: $e', 0);
    }
  }
  
  Future<ApiResponse<Resume>> uploadResume(File file) async {
    if (useMockData) {
      await Future.delayed(const Duration(seconds: 1));
      final newResume = Resume(
        id: 'resume_${DateTime.now().millisecondsSinceEpoch}',
        fileName: file.path.split('/').last,
        fileUrl: 'https://example.com/resumes/${file.path.split('/').last}',
        uploadedAt: DateTime.now(),
        score: AtsScore(
          overallScore: 75,
          keywordsScore: 70,
          formatScore: 85,
          experienceScore: 72,
          educationScore: 78,
          matchedKeywords: ['Python', 'Django', 'Flutter', 'REST API'],
          missingKeywords: ['AWS', 'Docker', 'Kubernetes'],
          suggestions: [
            'Add more quantifiable achievements',
            'Include relevant certifications',
            'Optimize skills section for ATS',
          ],
        ),
      );
      return ApiResponse.success(newResume, 201);
    }
    
    try {
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/resumes'),
      );
      request.headers.addAll(_headers);
      request.files.add(await http.MultipartFile.fromPath('file', file.path));
      
      final streamedResponse = await _httpClient.send(request);
      final response = await http.Response.fromStream(streamedResponse);
      
      if (response.statusCode == 201) {
        return ApiResponse.success(
          Resume.fromJson(jsonDecode(response.body)),
          response.statusCode,
        );
      }
      return ApiResponse.failure('Upload failed', response.statusCode);
    } on SocketException {
      return ApiResponse.failure('No internet connection', 0);
    } catch (e) {
      return ApiResponse.failure('An error occurred: $e', 0);
    }
  }
  
  Future<ApiResponse<AtsScore>> scoreResume(String resumeId) async {
    if (useMockData) {
      await Future.delayed(const Duration(seconds: 2));
      return ApiResponse.success(_mockScores[resumeId] ?? _generateRandomScore(), 200);
    }
    
    try {
      final response = await _httpClient.post(
        Uri.parse('$baseUrl/resumes/$resumeId/score'),
        headers: _headers,
      );
      
      if (response.statusCode == 200) {
        return ApiResponse.success(
          AtsScore.fromJson(jsonDecode(response.body)),
          response.statusCode,
        );
      }
      return ApiResponse.failure('Scoring failed', response.statusCode);
    } on SocketException {
      return ApiResponse.failure('No internet connection', 0);
    } catch (e) {
      return ApiResponse.failure('An error occurred: $e', 0);
    }
  }
  
  Future<ApiResponse<void>> deleteResume(String resumeId) async {
    if (useMockData) {
      await Future.delayed(const Duration(milliseconds: 500));
      return ApiResponse.success(null, 204);
    }
    
    try {
      final response = await _httpClient.delete(
        Uri.parse('$baseUrl/resumes/$resumeId'),
        headers: _headers,
      );
      
      if (response.statusCode == 204) {
        return ApiResponse.success(null, response.statusCode);
      }
      return ApiResponse.failure('Delete failed', response.statusCode);
    } on SocketException {
      return ApiResponse.failure('No internet connection', 0);
    } catch (e) {
      return ApiResponse.failure('An error occurred: $e', 0);
    }
  }
  
  // ============ JOBS ENDPOINTS ============
  
  Future<ApiResponse<List<Job>>> getJobs({
    int page = 1,
    int limit = 20,
    String? search,
    String? location,
  }) async {
    if (useMockData) {
      await Future.delayed(const Duration(milliseconds: 600));
      var jobs = _mockJobs;
      if (search != null && search.isNotEmpty) {
        jobs = jobs.where((job) =>
          job.title.toLowerCase().contains(search.toLowerCase()) ||
          job.company.toLowerCase().contains(search.toLowerCase())
        ).toList();
      }
      return ApiResponse.success(jobs, 200);
    }
    
    try {
      final queryParams = {
        'page': page.toString(),
        'limit': limit.toString(),
        if (search != null) 'search': search,
        if (location != null) 'location': location,
      };
      
      final uri = Uri.parse('$baseUrl/jobs').replace(queryParameters: queryParams);
      final response = await _httpClient.get(uri, headers: _headers);
      
      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return ApiResponse.success(
          data.map((json) => Job.fromJson(json)).toList(),
          response.statusCode,
        );
      }
      return ApiResponse.failure('Failed to fetch jobs', response.statusCode);
    } on SocketException {
      return ApiResponse.failure('No internet connection', 0);
    } catch (e) {
      return ApiResponse.failure('An error occurred: $e', 0);
    }
  }
  
  Future<ApiResponse<List<Job>>> getSavedJobs() async {
    if (useMockData) {
      await Future.delayed(const Duration(milliseconds: 500));
      return ApiResponse.success(
        _mockJobs.where((job) => job.isSaved).toList(),
        200,
      );
    }
    
    try {
      final response = await _httpClient.get(
        Uri.parse('$baseUrl/jobs/saved'),
        headers: _headers,
      );
      
      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return ApiResponse.success(
          data.map((json) => Job.fromJson(json)).toList(),
          response.statusCode,
        );
      }
      return ApiResponse.failure('Failed to fetch saved jobs', response.statusCode);
    } on SocketException {
      return ApiResponse.failure('No internet connection', 0);
    } catch (e) {
      return ApiResponse.failure('An error occurred: $e', 0);
    }
  }
  
  Future<ApiResponse<void>> toggleSaveJob(String jobId) async {
    if (useMockData) {
      await Future.delayed(const Duration(milliseconds: 300));
      return ApiResponse.success(null, 200);
    }
    
    try {
      final response = await _httpClient.post(
        Uri.parse('$baseUrl/jobs/$jobId/save'),
        headers: _headers,
      );
      
      if (response.statusCode == 200) {
        return ApiResponse.success(null, response.statusCode);
      }
      return ApiResponse.failure('Failed to save job', response.statusCode);
    } on SocketException {
      return ApiResponse.failure('No internet connection', 0);
    } catch (e) {
      return ApiResponse.failure('An error occurred: $e', 0);
    }
  }
  
  Future<ApiResponse<Job>> getJobDetails(String jobId) async {
    if (useMockData) {
      await Future.delayed(const Duration(milliseconds: 400));
      final job = _mockJobs.firstWhere(
        (j) => j.id == jobId,
        orElse: () => _mockJobs.first,
      );
      return ApiResponse.success(job, 200);
    }
    
    try {
      final response = await _httpClient.get(
        Uri.parse('$baseUrl/jobs/$jobId'),
        headers: _headers,
      );
      
      if (response.statusCode == 200) {
        return ApiResponse.success(
          Job.fromJson(jsonDecode(response.body)),
          response.statusCode,
        );
      }
      return ApiResponse.failure('Failed to fetch job details', response.statusCode);
    } on SocketException {
      return ApiResponse.failure('No internet connection', 0);
    } catch (e) {
      return ApiResponse.failure('An error occurred: $e', 0);
    }
  }
  
  Future<ApiResponse<Job>> getJobFromQr(String qrData) async {
    if (useMockData) {
      await Future.delayed(const Duration(milliseconds: 500));
      return ApiResponse.success(_mockJobs.first, 200);
    }
    
    try {
      final response = await _httpClient.get(
        Uri.parse('$baseUrl/jobs/qr/$qrData'),
        headers: _headers,
      );
      
      if (response.statusCode == 200) {
        return ApiResponse.success(
          Job.fromJson(jsonDecode(response.body)),
          response.statusCode,
        );
      }
      return ApiResponse.failure('Job not found', response.statusCode);
    } on SocketException {
      return ApiResponse.failure('No internet connection', 0);
    } catch (e) {
      return ApiResponse.failure('An error occurred: $e', 0);
    }
  }
  
  // ============ MOCK DATA ============
  
  static final List<Resume> _mockResumes = [
    Resume(
      id: 'resume_1',
      fileName: 'john_doe_resume.pdf',
      fileUrl: 'https://example.com/resumes/john_doe_resume.pdf',
      uploadedAt: DateTime.now().subtract(const Duration(days: 7)),
      score: AtsScore(
        overallScore: 82,
        keywordsScore: 78,
        formatScore: 90,
        experienceScore: 85,
        educationScore: 80,
        matchedKeywords: ['Python', 'JavaScript', 'React', 'Node.js', 'SQL'],
        missingKeywords: ['AWS', 'Docker', 'Kubernetes', 'CI/CD'],
        suggestions: [
          'Add more quantifiable achievements with numbers',
          'Include AWS or cloud certifications',
          'Add Docker/Kubernetes experience',
        ],
      ),
    ),
    Resume(
      id: 'resume_2',
      fileName: 'jane_smith_cv.pdf',
      fileUrl: 'https://example.com/resumes/jane_smith_cv.pdf',
      uploadedAt: DateTime.now().subtract(const Duration(days: 14)),
      score: AtsScore(
        overallScore: 91,
        keywordsScore: 95,
        formatScore: 88,
        experienceScore: 90,
        educationScore: 92,
        matchedKeywords: ['Flutter', 'Dart', 'Firebase', 'REST API', 'Agile'],
        missingKeywords: ['GraphQL'],
        suggestions: [
          'Consider adding GraphQL experience',
          'Add more mobile-specific achievements',
        ],
      ),
    ),
  ];
  
  static final Map<String, AtsScore> _mockScores = {
    'resume_1': AtsScore(
      overallScore: 82,
      keywordsScore: 78,
      formatScore: 90,
      experienceScore: 85,
      educationScore: 80,
      matchedKeywords: ['Python', 'JavaScript', 'React', 'Node.js', 'SQL'],
      missingKeywords: ['AWS', 'Docker', 'Kubernetes', 'CI/CD'],
      suggestions: [
        'Add more quantifiable achievements with numbers',
        'Include AWS or cloud certifications',
        'Add Docker/Kubernetes experience',
      ],
    ),
    'resume_2': AtsScore(
      overallScore: 91,
      keywordsScore: 95,
      formatScore: 88,
      experienceScore: 90,
      educationScore: 92,
      matchedKeywords: ['Flutter', 'Dart', 'Firebase', 'REST API', 'Agile'],
      missingKeywords: ['GraphQL'],
      suggestions: [
        'Consider adding GraphQL experience',
        'Add more mobile-specific achievements',
      ],
    ),
  };
  
  static final List<Job> _mockJobs = [
    Job(
      id: 'job_1',
      title: 'Senior Flutter Developer',
      company: 'TechCorp Inc.',
      location: 'San Francisco, CA (Remote)',
      salary: '\$140,000 - \$180,000',
      jobType: 'Full-time',
      postedAt: DateTime.now().subtract(const Duration(hours: 5)),
      matchScore: AtsScore(overallScore: 92),
      isSaved: true,
      description: '''We're looking for an experienced Flutter developer to join our mobile team.

Requirements:
- 4+ years of mobile development experience
- 2+ years of Flutter/Dart
- Strong state management (Provider, Riverpod, or BLoC)
- Experience with REST APIs and Firebase
- Familiarity with CI/CD pipelines

Benefits:
- Competitive salary
- Health, dental, and vision insurance
- 401(k) matching
- Flexible work hours
- Remote work options''',
    ),
    Job(
      id: 'job_2',
      title: 'Full Stack Engineer',
      company: 'StartupXYZ',
      location: 'New York, NY',
      salary: '\$120,000 - \$160,000',
      jobType: 'Full-time',
      postedAt: DateTime.now().subtract(const Duration(days: 1)),
      matchScore: AtsScore(overallScore: 78),
      isSaved: true,
      description: '''Join our growing team as a Full Stack Engineer.

Requirements:
- 3+ years of experience in full-stack development
- Proficiency in Python/Django or Node.js
- Experience with React or Vue.js
- SQL and NoSQL database experience
- RESTful API design

What we offer:
- Equity package
- Health benefits
- Professional development budget
- Modern office in Manhattan''',
    ),
    Job(
      id: 'job_3',
      title: 'Junior Python Developer',
      company: 'DataDriven LLC',
      location: 'Austin, TX (Hybrid)',
      salary: '\$75,000 - \$95,000',
      jobType: 'Full-time',
      postedAt: DateTime.now().subtract(const Duration(days: 2)),
      matchScore: AtsScore(overallScore: 65),
      isSaved: false,
      description: '''Great opportunity for a junior Python developer.

Requirements:
- 1+ years of Python experience
- Basic understanding of web frameworks (Django/Flask)
- Familiarity with databases
- Strong problem-solving skills

Benefits:
- Mentorship program
- Training budget
- Health insurance
- Monthly team events''',
    ),
    Job(
      id: 'job_4',
      title: 'DevOps Engineer',
      company: 'CloudScale Systems',
      location: 'Seattle, WA (Remote)',
      salary: '\$130,000 - \$170,000',
      jobType: 'Full-time',
      postedAt: DateTime.now().subtract(const Duration(days: 3)),
      matchScore: AtsScore(overallScore: 45),
      isSaved: false,
      description: '''Looking for a DevOps engineer to manage our infrastructure.

Requirements:
- 3+ years of DevOps experience
- AWS/Azure/GCP certification preferred
- Docker and Kubernetes expertise
- CI/CD pipeline experience
- Infrastructure as Code (Terraform)

We offer:
- Fully remote position
- Stock options
- Unlimited PTO
- Home office stipend''',
    ),
    Job(
      id: 'job_5',
      title: 'Mobile App Designer',
      company: 'CreativeStudio',
      location: 'Los Angeles, CA',
      salary: '\$90,000 - \$120,000',
      jobType: 'Contract',
      postedAt: DateTime.now().subtract(const Duration(days: 4)),
      matchScore: AtsScore(overallScore: 88),
      isSaved: true,
      description: '''Create beautiful mobile experiences.

Requirements:
- 2+ years of mobile UI/UX design
- Proficiency in Figma
- Understanding of iOS and Android guidelines
- Experience with design systems
- Portfolio required

Benefits:
- Creative freedom
- Flexible schedule
- Team retreats
- Latest design tools''',
    ),
  ];
  
  AtsScore _generateRandomScore() {
    final score = 50 + (DateTime.now().millisecond % 50);
    return AtsScore(
      overallScore: score,
      keywordsScore: score - 5,
      formatScore: score + 3,
      experienceScore: score - 2,
      educationScore: score + 5,
      matchedKeywords: ['Flutter', 'Dart', 'Firebase'],
      missingKeywords: ['GraphQL', 'WebSockets'],
      suggestions: [
        'Consider adding more relevant keywords',
        'Optimize your experience section',
      ],
    );
  }
  
  void dispose() {
    _httpClient.close();
  }
}
