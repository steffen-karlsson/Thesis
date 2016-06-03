package dk.steffenkarlsson.sofa.networking;

import android.app.Activity;
import android.content.Context;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.os.AsyncTask;
import android.os.Handler;
import android.util.Log;

import com.squareup.okhttp.Cache;
import com.squareup.okhttp.Call;
import com.squareup.okhttp.Callback;
import com.squareup.okhttp.MediaType;
import com.squareup.okhttp.OkHttpClient;
import com.squareup.okhttp.Request;
import com.squareup.okhttp.Response;

import java.io.File;
import java.io.IOException;

/**
 * Created by steffenkarlsson on 22/12/14.
 */
@SuppressWarnings("ALL")
public abstract class BaseRequest<T> {

    private static final String TAG = "Networking >>>";
    private static String mAuthentication;
    private static Class<?> _clazz;

    protected final MediaType json = MediaType.parse("application/json; charset=utf-8");
    protected final MediaType text = MediaType.parse("application/text; charset=utf-8");

    public interface OnRequestListener {
        void onError(int id, int statusCode);

        void onError(int id, int statusCode, Object error);

        void onSuccess(int id, Result result);

        void onProcessing();
    }

    private static final OkHttpClient mClient = new OkHttpClient();

    private String mUrl;
    private boolean mIsAsync;
    private Activity mActivity;
    private int mRequestId = -1;

    protected OnRequestListener mOnRequestListener;

    protected BaseRequest(String url) {
        this.mUrl = url;
    }

    public void runAsync(Enum requestIdentifier) {
        run(requestIdentifier, true);
    }

    public void runAsync() {
        run(null, true);
    }

    public void run(Enum requestIdentifier) {
        run(requestIdentifier, false);
    }

    public void run() {
        run(null, false);
    }

    private void run(Enum requestIdentifier, boolean isAsync) {
        if (mActivity == null) {
            Log.e(TAG, "No context defined");
            return;
        }

        if (mOnRequestListener == null) {
            Log.e(TAG, "No listener defined: OnRequestListener");
            return;
        }

        if (requestIdentifier != null) {
            this.mRequestId = RequestHandler.getIdFromRequestIdentifier(requestIdentifier);
        }

        this.mIsAsync = isAsync;

        if (isNetworkConnected(mActivity)) {
            new Downloader().execute(buildRequest());
        } else {
            reportError(ErrorCode.NO_NETWORK.code);
        }
    }

    private Callback mHttpCallBack = new Callback() {
        @Override
        public void onFailure(Request request, IOException e) {
        }

        @Override
        public void onResponse(Response response) throws IOException {
            try {
                handleResponse(response);
            } catch (ParserException ignore) {
                reportError(ErrorCode.PARSER_FAIL.code);
            }
        }
    };

    private void handleResponse(Response response) throws ParserException {
        final int statusCode = response.code();
        try {
            String res = response.body().string();
            Log.d(TAG, "Response: " + res);

            if (response.isSuccessful()) {
                if (statusCode == 204) {
                    postToMain(new Runnable() {
                        @Override
                        public void run() {
                            mOnRequestListener.onSuccess(mRequestId, new Result(statusCode, null));
                        }
                    });
                } else {
                    final Result<T> result = handleResponse(statusCode, res);
                    postToMain(new Runnable() {
                        @Override
                        public void run() {
                            mOnRequestListener.onSuccess(mRequestId, result);
                        }
                    });
                }

            } else {
                if (mOnRequestListener != null) {
                    if (_clazz != null) {
                        reportErrorWithObject(statusCode, RequestUtils.parse(_clazz, res));
                    } else {
                        reportError(statusCode);
                    }
                }
            }
        } catch (ParserException ignore) {
            reportError(ErrorCode.PARSER_FAIL.code);
        } catch (IOException e) {
            reportError(ErrorCode.NETWORK_ERROR.code);
        }
    }

    public abstract Result<T> handleResponse(int statusCode, String body) throws ParserException;

    protected Request buildRequest() {
        Log.d(TAG, "URL: " + mUrl);
        Request.Builder builder = new Request.Builder();
        builder.url(mUrl);
        builder.addHeader("Content-Type", "application/json");

        if (shouldUseAuthentication()) {
            builder.addHeader("Authorization", "Basic " + mAuthentication);
        }

        return finalizeRequest(builder);
    }

    public static void setBasicAuthentication(String authentication) {
        mAuthentication = authentication;
    }

    public static void setDefaultErrorClass(Class<?> clazz) {
        _clazz = clazz;
    }

    protected boolean shouldUseAuthentication() {
        return true;
    }

    /**
     * If overriding, do not call super, but call builder.build() as last part of the
     * implementation instead.
     *
     * @param builder
     * @return Request
     */
    protected Request finalizeRequest(Request.Builder builder) {
        return builder.build();
    }

    /**
     * Call method once.
     *
     * @param cacheDirectory
     * @param size
     * @throws IOException
     */
    public static void useCache(File cacheDirectory, long size) throws IOException {
        mClient.setCache(new Cache(cacheDirectory, size));
    }

    public BaseRequest setOnRequestListener(OnRequestListener onRequestListener) {
        this.mOnRequestListener = onRequestListener;
        return this;
    }

    public BaseRequest withContext(Activity activity) {
        this.mActivity = activity;
        return this;
    }

    /**
     * Using GSON parser as default
     *
     * @param body
     * @return
     */
    protected abstract T parseHttpResponseBody(String body) throws ParserException;

    private boolean isNetworkConnected(Context context) {
        ConnectivityManager cm = (ConnectivityManager) context.getSystemService(Context.CONNECTIVITY_SERVICE);
        NetworkInfo info = cm.getActiveNetworkInfo();
        return info != null && info.isConnectedOrConnecting();
    }

    private class Downloader extends AsyncTask<Request, Integer, Object> {

        @Override
        protected Object doInBackground(Request... params) {
            try {
                Call call = mClient.newCall(params[0]);
                postToMain(new Runnable() {
                    @Override
                    public void run() {
                        mOnRequestListener.onProcessing();
                    }
                });
                if (mIsAsync) {
                    call.enqueue(mHttpCallBack);
                } else {
                    try {
                        Response response = call.execute();
                        handleResponse(response);
                    } catch (ParserException ignore) {
                        reportError(ErrorCode.PARSER_FAIL.code);
                    }
                }
            } catch (IOException e) {
                reportError(ErrorCode.NETWORK_ERROR.code);
            }
            return null;
        }
    }

    protected void reportError(final int errorCode) {
        postToMain(new Runnable() {
            @Override
            public void run() {
                mOnRequestListener.onError(mRequestId, errorCode);
            }
        });
    }

    protected void reportErrorWithObject(final int statusCode, final Object error) {
        postToMain(new Runnable() {
            @Override
            public void run() {
                mOnRequestListener.onError(mRequestId, statusCode, error);
            }
        });
    }

    protected void postToMain(Runnable runnable) {
        new Handler(mActivity.getMainLooper()).post(runnable);
    }

}