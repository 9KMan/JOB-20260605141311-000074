import 'package:flutter/material.dart';
import 'package:percent_indicator/circular_percent_indicator.dart';

import '../api/client.dart';

/// Reusable score display widget.
///
/// Shows:
/// - Circular progress (0-100)
/// - Letter grade badge (A-F)
/// - Color coded: green ≥80, yellow 60-79, red <60
/// - Optional matched/missing skill counts
class ScoreCard extends StatelessWidget {
  final double score;
  final String? grade;
  final String? label;
  final int? matchedCount;
  final int? missingCount;
  final VoidCallback? onTap;
  final bool compact;

  const ScoreCard({
    super.key,
    required this.score,
    this.grade,
    this.label,
    this.matchedCount,
    this.missingCount,
    this.onTap,
    this.compact = false,
  });

  Color get _color {
    if (score >= 80) return Colors.green.shade600;
    if (score >= 60) return Colors.amber.shade700;
    return Colors.red.shade400;
  }

  String get _gradeLetter {
    if (grade != null) return grade!;
    if (score >= 90) return 'A';
    if (score >= 80) return 'B';
    if (score >= 70) return 'C';
    if (score >= 60) return 'D';
    return 'F';
  }

  @override
  Widget build(BuildContext context) {
    final pct = (score / 100).clamp(0.0, 1.0);
    final size = compact ? 60.0 : 120.0;

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              CircularPercentIndicator(
                radius: size / 2,
                lineWidth: compact ? 6 : 10,
                percent: pct,
                center: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      score.toStringAsFixed(0),
                      style: TextStyle(
                        fontSize: compact ? 16 : 28,
                        fontWeight: FontWeight.bold,
                        color: _color,
                      ),
                    ),
                    if (!compact)
                      Text(
                        _gradeLetter,
                        style: TextStyle(
                          fontSize: 12,
                          color: _color,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                  ],
                ),
                progressColor: _color,
                backgroundColor: _color.withValues(alpha: 0.15),
                circularStrokeCap: CircularStrokeCap.round,
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (label != null)
                      Text(
                        label!,
                        style: TextStyle(
                          fontSize: compact ? 12 : 14,
                          fontWeight: FontWeight.w600,
                          color: Colors.grey.shade700,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    if (label != null) const SizedBox(height: 4),
                    Text(
                      _gradeLetter == 'A' || _gradeLetter == 'B'
                          ? 'Strong match'
                          : _gradeLetter == 'C'
                              ? 'Decent match'
                              : 'Needs work',
                      style: TextStyle(
                        fontSize: compact ? 14 : 18,
                        fontWeight: FontWeight.bold,
                        color: _color,
                      ),
                    ),
                    if (matchedCount != null || missingCount != null) ...[
                      const SizedBox(height: 6),
                      Row(
                        children: [
                          if (matchedCount != null) ...[
                            Icon(Icons.check_circle,
                                size: 14, color: Colors.green.shade600),
                            const SizedBox(width: 2),
                            Text(
                              '$matchedCount',
                              style: const TextStyle(fontSize: 12),
                            ),
                            const SizedBox(width: 12),
                          ],
                          if (missingCount != null) ...[
                            Icon(Icons.cancel,
                                size: 14, color: Colors.red.shade400),
                            const SizedBox(width: 2),
                            Text(
                              '$missingCount',
                              style: const TextStyle(fontSize: 12),
                            ),
                          ],
                        ],
                      ),
                    ],
                  ],
                ),
              ),
              if (onTap != null)
                Icon(Icons.chevron_right, color: Colors.grey.shade400),
            ],
          ),
        ),
      ),
    );
  }
}

/// Compact score badge (for lists).
class ScoreBadge extends StatelessWidget {
  final double score;
  const ScoreBadge({super.key, required this.score});

  Color get _color {
    if (score >= 80) return Colors.green.shade600;
    if (score >= 60) return Colors.amber.shade700;
    return Colors.red.shade400;
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: _color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: _color, width: 1),
      ),
      child: Text(
        score.toStringAsFixed(0),
        style: TextStyle(
          color: _color,
          fontWeight: FontWeight.bold,
          fontSize: 12,
        ),
      ),
    );
  }
}
