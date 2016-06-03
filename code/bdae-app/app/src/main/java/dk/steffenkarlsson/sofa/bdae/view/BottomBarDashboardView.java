package dk.steffenkarlsson.sofa.bdae.view;

import android.content.Context;
import android.content.DialogInterface;
import android.support.design.widget.FloatingActionButton;
import android.support.v4.view.LayoutInflaterCompat;
import android.support.v7.app.AlertDialog;
import android.support.v7.view.ContextThemeWrapper;
import android.text.SpannableString;
import android.text.Spanned;
import android.text.style.ForegroundColorSpan;
import android.util.AttributeSet;
import android.view.LayoutInflater;
import android.webkit.WebView;
import android.widget.TextView;

import java.util.List;

import butterknife.BindView;
import butterknife.OnClick;
import dk.steffenkarlsson.sofa.bdae.IActivityHandler;
import dk.steffenkarlsson.sofa.bdae.JobResultActivity;
import dk.steffenkarlsson.sofa.bdae.R;
import dk.steffenkarlsson.sofa.bdae.SubmitJobActivity;
import dk.steffenkarlsson.sofa.bdae.entity.Job;
import dk.steffenkarlsson.sofa.bdae.extra.CustomRequestListener;
import dk.steffenkarlsson.sofa.bdae.extra.DataTypeHelper;
import dk.steffenkarlsson.sofa.bdae.extra.TransitionAnimation;
import dk.steffenkarlsson.sofa.bdae.recycler.GenericRecyclerViewModel;
import dk.steffenkarlsson.sofa.bdae.recycler.SubmittedJobRecyclerView;
import dk.steffenkarlsson.sofa.bdae.request.GetSubmittedJobsRequest;
import dk.steffenkarlsson.sofa.networking.Result;

/**
 * Created by steffenkarlsson on 5/31/16.
 */
public class BottomBarDashboardView extends BottomPagerControllerRecyclerView {

    public enum RequestType {
        JOBS
    }

    @BindView(R.id.fab)
    protected FloatingActionButton mAddNewJob;

    public BottomBarDashboardView(Context context) {
        super(context);
    }

    public BottomBarDashboardView(Context context, AttributeSet attrs) {
        super(context, attrs);
    }

    @Override
    public boolean hasOptionsMenu() {
        return false;
    }

    @Override
    public void setContent(IActivityHandler handler) {
        super.setContent(handler);

        CustomRequestListener listener = new CustomRequestListener(mActivityHandler) {
            @Override
            protected void onData(int id, Result result) {
                List<Job> jobs = (List<Job>) result.response;

                for (Job job : jobs) {
                    job.setOnClickListener(new SubmittedJobRecyclerView.OnClickListener() {
                        @Override
                        public void onCellClick(final String function, final String result, final String dataType) {
                            SpannableString title = new SpannableString(function);
                            title.setSpan(new ForegroundColorSpan(getResources().getColor(R.color.colorPrimary)), 0, function.length(), Spanned.SPAN_INCLUSIVE_INCLUSIVE);

                            AlertDialog alertDialog = new AlertDialog.Builder(mActivityHandler.getActivity())
                                    .setTitle(title)
                                    .create();

                            alertDialog.setButton(AlertDialog.BUTTON_NEGATIVE,
                                    getResources().getString(R.string.close), new DialogInterface.OnClickListener() {
                                        @Override
                                        public void onClick(DialogInterface dialog, int which) {
                                            dialog.dismiss();
                                        }
                                    });

                            if (JobResultActivity.isSupported(dataType)) {
                                alertDialog.setButton(AlertDialog.BUTTON_NEUTRAL,
                                        getResources().getString(R.string.open_fullscreen), new DialogInterface.OnClickListener() {
                                            @Override
                                            public void onClick(DialogInterface dialog, int which) {
                                                mActivityHandler.launchActivity(mActivityHandler.getActivityIntent(
                                                        mActivityHandler.getContext(),
                                                        JobResultActivity.class,
                                                        JobResultActivity.getBundleArgs(function, result, dataType),
                                                        false), TransitionAnimation.IN_FROM_RIGHT);
                                                dialog.dismiss();
                                            }
                                        });

                                WebView resultView = new WebView(getContext());
                                resultView.getSettings().setJavaScriptEnabled(true);
                                resultView.getSettings().setLoadWithOverviewMode(true);
                                resultView.getSettings().setUseWideViewPort(true);
                                resultView.loadDataWithBaseURL("", DataTypeHelper.getHTML(
                                        mActivityHandler.getActivity(), result, dataType), "text/html", "UTF-8", "");

                                alertDialog.setView(resultView);
                            } else {
                                alertDialog.setMessage(getResources().getString(R.string.job_result, result));
                            }

                            alertDialog.show();
                        }

                        @Override
                        public void onArgumentsClick() {

                        }
                    });
                    mAdapter.add(new GenericRecyclerViewModel(job, SubmittedJobRecyclerView.class));
                }

                mAdapter.notifyDataSetChanged();
            }

            @Override
            public void onError(int id, int statusCode) {
                //TODO: Handle error
            }
        };

        new GetSubmittedJobsRequest()
                .withContext(handler.getActivity())
                .setOnRequestListener(listener)
                .run(RequestType.JOBS);
    }

    @Override
    protected int getLayoutResource() {
        return R.layout.content_dashboard_view;
    }

    @OnClick(R.id.fab)
    public void onFabClicked() {
        mActivityHandler.launchActivity(mActivityHandler.getActivityIntent(
                mActivityHandler.getContext(), SubmitJobActivity.class, false),
                TransitionAnimation.IN_FROM_BOTTOM);
    }
}
